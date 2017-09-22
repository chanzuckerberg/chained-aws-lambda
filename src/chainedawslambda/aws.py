import json
import logging
import traceback
import typing
import uuid

import boto3

from . import _awstest, awsconstants
from ._awsimpl import AWSRuntime
from .base import Task
from .runner import Runner

logger = logging.getLogger()
logger.setLevel(logging.INFO)


clients = dict()  # type: typing.MutableMapping[str, typing.Type[Task]]


# this is the authoritative mapping between client names and Task classes.
def get_clients() -> typing.MutableMapping[str, typing.Type[Task]]:
    return clients


def add_client(client_name: str, client_class: typing.Type[Task]):
    clients[client_name] = client_class


def resolve_class(task_class: typing.Type[Task]):
    clients = get_clients()
    for client_name, client_class in clients.items():
        if client_class == task_class:
            break
    else:
        raise ValueError(f"Unknown task class {task_class}.")

    return client_name


def schedule_task(task_class: typing.Type[Task[dict, typing.Any]], state: dict, task_id: str=None) -> str:
    """
    Schedule or reschedule a task for execution.  If it's a new task, task_id should be None.  If it's the resumption of
    an existing task, then task_id should be the original task's task_id.
    """
    client_name = resolve_class(task_class)

    if task_id is None:
        task_id = str(uuid.uuid4())
        action = awsconstants.LogActions.SCHEDULED
    else:
        action = awsconstants.LogActions.RESCHEDULED

    payload = {
        awsconstants.CLIENT_KEY: client_name,
        awsconstants.REQUEST_VERSION_KEY: awsconstants.CURRENT_VERSION,
        awsconstants.TASK_ID_KEY: task_id,
        awsconstants.STATE_KEY: state,
    }

    sts_client = boto3.client("sts")
    accountid = sts_client.get_caller_identity()['Account']

    sns_client = boto3.client("sns")
    region = boto3.Session().region_name
    arn = f"arn:aws:sns:{region}:{accountid}:{client_name}"
    sns_client.publish(
        TopicArn=arn,
        Message=json.dumps(payload),
    )

    AWSRuntime.log(
        client_name,
        task_id,
        json.dumps(dict(
            action=action,
            payload=payload,
        )),
    )

    return task_id


def parse_payload(payload: dict, expected_client_name: str):
    try:
        task_id = payload[awsconstants.TASK_ID_KEY]
    except KeyError as ex:
        AWSRuntime.log(
            expected_client_name,
            awsconstants.FALLBACK_LOG_STREAM_NAME,
            json.dumps(dict(
                action=awsconstants.LogActions.EXCEPTION,
                message="Could not find task_id",
                payload=payload,
                exception=str(ex),
                stacktrace=traceback.format_exc(),
            )),
        )
        return None

    # look up by client name
    try:
        client_name = payload[awsconstants.CLIENT_KEY]
        client_class = get_clients()[client_name]
        version = payload[awsconstants.REQUEST_VERSION_KEY]
        state = payload[awsconstants.STATE_KEY]
    except KeyError as ex:
        AWSRuntime.log(
            expected_client_name,
            task_id,
            json.dumps(dict(
                action=awsconstants.LogActions.EXCEPTION,
                message="Request payload missing required data",
                payload=payload,
                exception=str(ex),
                stacktrace=traceback.format_exc(),
                valid_clients=str(get_clients()),
            )),
        )
        return None

    if client_name != expected_client_name:
        AWSRuntime.log(
            expected_client_name,
            task_id,
            json.dumps(dict(
                action=awsconstants.LogActions.MISMATCHED_CLIENTS,
                client_name=client_name,
                expected_client_name=expected_client_name,
                state=state,
            )),
        )
        return

    if version < awsconstants.MIN_SUPPORTED_VERSION or version > awsconstants.MAX_SUPPORTED_VERSION:
        AWSRuntime.log(
            expected_client_name,
            task_id,
            json.dumps(dict(
                action=awsconstants.LogActions.EXCEPTION,
                message="Message version not supported",
                payload=payload,
            )),
        )
        return None

    return task_id, client_name, client_class, state


def dispatch(context, payload, expected_client_name):
    decoded_payload = parse_payload(payload, expected_client_name)
    if decoded_payload is None:
        return
    task_id, client_name, client_class, state = decoded_payload

    AWSRuntime.log(
        expected_client_name,
        task_id,
        json.dumps(dict(
            action=awsconstants.LogActions.RUNNING,
            state=state,
        )),
    )

    if client_name != expected_client_name:
        AWSRuntime.log(
            task_id,
            json.dumps(dict(
                action=awsconstants.LogActions.MISMATCHED_CLIENTS,
                client_name=client_name,
                expected_client_name=expected_client_name,
                state=state,
            )),
        )
        return

    try:
        # special case: if the client name is `AWS_FAST_TEST_CLIENT_NAME`, we use a special runtime environment so we
        # don't take forever running the test.
        if client_class == _awstest.AWSFastTestTask:
            runtime = _awstest.AWSFastTestRuntime(context, client_name, task_id)
        else:
            runtime = AWSRuntime(context, client_name, task_id)

        task = client_class(state, runtime=runtime)

        runner = Runner(task, runtime)
        runner.run()
    except Exception as ex:
        AWSRuntime.log(
            expected_client_name,
            task_id,
            json.dumps(dict(
                action=awsconstants.LogActions.EXCEPTION,
                stacktrace=traceback.format_exc(),
            )),
        )
        raise

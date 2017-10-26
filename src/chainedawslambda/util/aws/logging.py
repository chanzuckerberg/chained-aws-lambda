import time
import typing

import boto3


def scan_logs(filter_args: dict, log_consumer: typing.Callable[[typing.Optional[str]], typing.Any]):
    """
    Scan AWS Cloudwatch logs and feed the results into a callable.  The callable should return a non-None value if it
    wishes to exit the scan, and that value is returned to the caller of `scan_logs`.

    When there are no more log entries, the callable is called with a `None` argument, and the return value is returned
    to the caller of `scan_logs`.
    """
    logs_client = boto3.client('logs')
    paginator = logs_client.get_paginator('filter_log_events')
    response = paginator.paginate(**filter_args)

    for page in response:
        for event in page['events']:
            result = log_consumer(event['message'])
            if result is not None:
                return result

    return log_consumer(None)


def log_message(log_group_name: str, log_stream_name: str, message: str):
    """Logs a message to cloudwatch."""

    logs_client = boto3.client("logs")

    def get_sequence_token():
        # try to get the upload sequence token
        paginator = logs_client.get_paginator('describe_log_streams')
        for page in paginator.paginate(logGroupName=log_group_name, logStreamNamePrefix=log_stream_name):
            for log_stream in page['logStreams']:
                if log_stream['logStreamName'] == log_stream_name:
                    return log_stream.get('uploadSequenceToken', None)

        return None

    while True:
        try:
            logs_client.create_log_group(logGroupName=log_group_name)
        except logs_client.exceptions.ResourceAlreadyExistsException:
            pass
        try:
            logs_client.create_log_stream(
                logGroupName=log_group_name, logStreamName=log_stream_name)
        except logs_client.exceptions.ResourceAlreadyExistsException:
            pass

        sequence_token = get_sequence_token()

        try:
            kwargs = dict(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                logEvents=[dict(
                    timestamp=int(time.time() * 1000),
                    message=message,
                )],
            )
            if sequence_token is not None:
                kwargs['sequenceToken'] = sequence_token

            logs_client.put_log_events(**kwargs)
            break
        except logs_client.exceptions.InvalidSequenceTokenException:
            pass

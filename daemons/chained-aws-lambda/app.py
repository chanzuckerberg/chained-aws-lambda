import json
import os
import sys

import domovoi

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'domovoilib'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import dss
from dss.events.chainedawslambda import aws
from dss.events.chainedawslambda import awsconstants

app = domovoi.Domovoi()

expected_client_name = os.getenv("CHAINED_AWS_LAMBDA_CLIENT_NAME")
worker_sns_topic = awsconstants.get_worker_sns_topic(expected_client_name)


@app.sns_topic_subscriber(worker_sns_topic)
def process_work(event: dict, context) -> None:
    payload = json.loads(event["Records"][0]["Sns"]["Message"])
    aws.dispatch(context, payload, expected_client_name)

import os

TASK_SNS_TOPIC_PREFIX = "chained-aws-lambda-"
TASK_RETRY_QUEUE_PREFIX = "chained-aws-lambda-"

CLIENT_KEY = "chained-aws-lambda"
REQUEST_VERSION_KEY = "request_version"
TASK_ID_KEY = "task_id"
STATE_KEY = "state"

FALLBACK_LOG_STREAM_NAME = "fallback"

CURRENT_VERSION = 1
MIN_SUPPORTED_VERSION = 1
MAX_SUPPORTED_VERSION = 1


# This should be an enum, but doing so makes it cumbersome to serialize to json.
class LogActions:
    SCHEDULED = "scheduled"
    RESCHEDULED = "rescheduled"
    RUNNING = "running"
    EXCEPTION = "exception"
    MISMATCHED_CLIENTS = "mismatched_clients"
    COMPLETE = "complete"


def get_worker_sns_topic(expected_client_name):
    deployment_stage = os.getenv("DEPLOYMENT_STAGE")
    return TASK_SNS_TOPIC_PREFIX + expected_client_name + "-" + deployment_stage

#!/bin/bash

set -euo pipefail

if [[ $# != 2 ]]; then
    echo "Usage: $(basename $0) daemon-name stage"
    exit 1
fi

export daemon_name=$1 stage=$2
stage_ucase=$(echo $stage | awk '{print toupper($0)}')
export lambda_name="${daemon_name}-${stage}" iam_role_name="${daemon_name}-${stage}"
deployed_json="$(dirname $0)/${daemon_name}/.chalice/deployed.json"
config_json="$(dirname $0)/${daemon_name}/.chalice/config.json"
policy_json="$(dirname $0)/${daemon_name}/.chalice/policy.json"
stage_policy_json="$(dirname $0)/${daemon_name}/.chalice/policy-${stage}.json"
policy_template="$(dirname $0)/../iam/policy-templates/${daemon_name}-lambda.json"
export account_id=$(aws sts get-caller-identity | jq -r .Account)

cat "$config_json" | jq ".stages.$stage.api_gateway_stage=env.stage" | sponge "$config_json"

export lambda_arn=$(aws lambda list-functions | jq -r '.Functions[] | select(.FunctionName==env.lambda_name) | .FunctionArn')
if [[ -z $lambda_arn ]]; then
    echo "Lambda function $lambda_name not found, resetting deploy config"
    rm -f "$deployed_json"
else
    jq -n ".$stage.api_handler_name = env.lambda_name | \
           .$stage.api_handler_arn = env.lambda_arn | \
           .$stage.rest_api_id = \"\" | \
           .$stage.region = env.AWS_DEFAULT_REGION | \
           .$stage.api_gateway_stage = null | \
           .$stage.backend = \"api\" | \
           .$stage.chalice_version = \"1.0.1\" | \
           .$stage.lambda_functions = {}" > "$deployed_json"
fi

for var in $EXPORT_ENV_VARS_TO_LAMBDA; do
    cat "$config_json" | jq .stages.$stage.environment_variables.$var=env.$var | sponge "$config_json"
done

if [[ ${CI:-} == true ]]; then
    export iam_role_arn=$(aws iam list-roles | jq -r '.Roles[] | select(.RoleName==env.iam_role_name) | .Arn')
    cat "$config_json" | jq .manage_iam_role=false | jq .iam_role_arn=env.iam_role_arn | sponge "$config_json"
fi

cat "$policy_template" | envsubst '$S3_BUCKET $account_id $stage' > "$policy_json"
cp "$policy_json" "$stage_policy_json"

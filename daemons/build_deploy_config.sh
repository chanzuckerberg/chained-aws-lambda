#!/bin/bash

set -euo pipefail

if [[ $# != 2 ]]; then
    echo "Usage: $(basename $0) daemon-name stage"
    exit 1
fi

export daemon_name=$1 stage=$2
export lambda_name="${daemon_name}-${stage}" iam_role_name="${daemon_name}-${stage}"
deployed_json="$(dirname $0)/${daemon_name}/.chalice/deployed.json"
config_json="$(dirname $0)/${daemon_name}/.chalice/config.json"
stage_policy_json="$(dirname $0)/${daemon_name}/.chalice/policy-${stage}.json"
account_id=$(aws sts get-caller-identity | jq -r .Account)

# set up the app skeleton.
rm -rf $daemon_name
cp -rf chained-aws-lambda $daemon_name
python ../scripts/chained_aws_lambda.py "${account_id}" \
	  --enable-s3-parallel-copy-supervisor --s3-parallel-copy-supervisor-lambda-name chained-aws-lambda-s3-parallel-copy-supervisor-dev \
	  --enable-s3-parallel-copy-worker --s3-parallel-copy-worker-lambda-name chained-aws-lambda-s3-parallel-copy-worker-dev \
	  --enable-s3-copy --s3-copy-lambda-name chained-aws-lambda-s3-copy-dev \
	  --enable-fasttest --fasttest-lambda-name chained-aws-lambda-fasttest-dev \
	  --enable-supervisortest --supervisortest-lambda-name chained-aws-lambda-supervisortest-dev \
	  --${daemon_name#chained-aws-lambda-}-policy-path "${stage_policy_json}" --${daemon_name#chained-aws-lambda-}-app-path $daemon_name/app.py

# set up the source code.
cp -R ../src/chainedawslambda "${daemon_name}/domovoilib"

# set up config.json
cat chained-aws-lambda/.chalice/config.json | jq '.app_name=env.daemon_name' > "${config_json}"
for var in $EXPORT_ENV_VARS_TO_LAMBDA; do
    cat "$config_json" | jq .stages.$stage.environment_variables.$var=env.$var | sponge "$config_json"
done

if [[ ${CI:-} == true ]]; then
    export iam_role_arn=$(aws iam list-roles | jq -r '.Roles[] | select(.RoleName==env.iam_role_name) | .Arn')
    cat "$config_json" | jq .manage_iam_role=false | jq .iam_role_arn=env.iam_role_arn | sponge "$config_json"
fi

# set up policy.json
cat "${stage_policy_json}" | jq -f s3_enable.filter | sponge "${stage_policy_json}"

# set up deployed.json
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

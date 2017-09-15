include ../common.mk

deploy: chained-aws-lambda

chainedawslambdatargets := $(shell ../scripts/get_all_chained_aws_lambda_clients.py)
chained-aws-lambda: $(chainedawslambdatargets)
$(chainedawslambdatargets): chained-aws-lambda-%:
	rm -rf $@
	cp -rf chained-aws-lambda $@
	cat chained-aws-lambda/.chalice/config.json | jq '.app_name="$@" | .stages.$(DEPLOYMENT_STAGE).environment_variables.CHAINED_AWS_LAMBDA_CLIENT_NAME="$*"' > $@/.chalice/config.json
	cp -R ../dss $@/domovoilib
	./build_deploy_config.sh $@ $(DEPLOYMENT_STAGE)
	cd $@; CHAINED_AWS_LAMBDA_CLIENT_NAME=$* domovoi deploy --stage $(DEPLOYMENT_STAGE)

.PHONY: chained-aws-lambda $(chainedawslambdatargets)

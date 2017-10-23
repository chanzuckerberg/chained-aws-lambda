include ../common.mk

deploy: chained-aws-lambda

chainedawslambdatargets := chained-aws-lambda-s3-parallel-copy-supervisor \
                           chained-aws-lambda-s3-parallel-copy-worker \
                           chained-aws-lambda-s3-copy \
                           chained-aws-lambda-fasttest \
                           chained-aws-lambda-supervisortest \

chainedawslambdaconfigtargets := $(addsuffix .config, $(chainedawslambdatargets))

chained-aws-lambda: $(chainedawslambdatargets)
$(chainedawslambdatargets): chained-aws-lambda-% : chained-aws-lambda-%.config
	cd $@; domovoi deploy --stage dev

$(chainedawslambdaconfigtargets): chained-aws-lambda-%.config :
	./build_deploy_config.sh chained-aws-lambda-$* dev

.PHONY: chained-aws-lambda $(chainedawslambdatargets) $(chainedawslambdaconfigtargets)

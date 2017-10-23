include ../common.mk

deploy: chained-aws-lambda

chainedawslambdatargets := chained-aws-lambda-s3-parallel-copy-supervisor \
                           chained-aws-lambda-s3-parallel-copy-worker \
                           chained-aws-lambda-s3-copy \
                           chained-aws-lambda-fasttest \
                           chained-aws-lambda-supervisortest \

chained-aws-lambda: $(chainedawslambdatargets)
$(chainedawslambdatargets):
	./build_deploy_config.sh $@ dev
	cd $@; domovoi deploy --stage dev

.PHONY: chained-aws-lambda $(chainedawslambdatargets)

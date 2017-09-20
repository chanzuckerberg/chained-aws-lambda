include ../common.mk

deploy: chained-aws-lambda

account_id := $(shell aws sts get-caller-identity | jq -r .Account)
chainedawslambdatargets := chained-aws-lambda-s3-parallel-copy-supervisor \
                           chained-aws-lambda-s3-parallel-copy-worker \
                           chained-aws-lambda-s3-copy \
                           chained-aws-lambda-fasttest \
                           chained-aws-lambda-supervisortest \

chained-aws-lambda: $(chainedawslambdatargets)
$(chainedawslambdatargets): chained-aws-lambda-%:
	rm -rf $@
	cp -rf chained-aws-lambda $@
	python ../scripts/chained_aws_lambda.py $(account_id) \
	  --enable-s3-parallel-copy-supervisor --s3-parallel-copy-supervisor-lambda-name chained-aws-lambda-s3-parallel-copy-supervisor-dev \
	  --enable-s3-parallel-copy-worker --s3-parallel-copy-worker-lambda-name chained-aws-lambda-s3-parallel-copy-worker-dev \
	  --enable-s3-copy --s3-copy-lambda-name chained-aws-lambda-s3-copy-dev \
	  --enable-fasttest --fasttest-lambda-name chained-aws-lambda-fasttest-dev \
	  --enable-supervisortest --supervisortest-lambda-name chained-aws-lambda-supervisortest-dev \
	  --$*-policy-path $@/.chalice/policy.json --$*-app-path $@/app.py

	cat chained-aws-lambda/.chalice/config.json | jq '.app_name="$@"' > $@/.chalice/config.json
	# blindly enable access to our test S3 bucket.  This is ok since most daemons require it anyway.
	cat $@/.chalice/policy.json | jq -f s3_enable.filter | sponge $@/.chalice/policy.json
	cp -R ../src/chainedawslambda $@/domovoilib
	./build_deploy_config.sh $@ dev
	cd $@; domovoi deploy --stage dev

.PHONY: chained-aws-lambda $(chainedawslambdatargets)

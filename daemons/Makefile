include ../common.mk

deploy: chained-aws-lambda

account_id := $(shell aws sts get-caller-identity | jq -r .Account)
chainedawslambdatargets := chained-aws-lambda-s3-parallel-copy-supervisor \
                           chained-aws-lambda-s3-parallel-copy-worker \
                           chained-aws-lambda-s3-copy \
                           chained-aws-lambda-fasttest \
                           chained-aws-lambda-supervisortest \

chainedawslambdaconfigtargets := $(addsuffix .config, $(chainedawslambdatargets))

chained-aws-lambda: $(chainedawslambdatargets)
$(chainedawslambdatargets): chained-aws-lambda-%: chained-aws-lambda-%.config
	cd chained-aws-lambda-$*; domovoi deploy --stage dev

$(chainedawslambdaconfigtargets): chained-aws-lambda-%.config :
	rm -rf chained-aws-lambda-$*
	cp -rf chained-aws-lambda chained-aws-lambda-$*
	python ../scripts/chained_aws_lambda.py $(account_id) \
	  --enable-s3-parallel-copy-supervisor --s3-parallel-copy-supervisor-lambda-name chained-aws-lambda-s3-parallel-copy-supervisor-dev \
	  --enable-s3-parallel-copy-worker --s3-parallel-copy-worker-lambda-name chained-aws-lambda-s3-parallel-copy-worker-dev \
	  --enable-s3-copy --s3-copy-lambda-name chained-aws-lambda-s3-copy-dev \
	  --enable-fasttest --fasttest-lambda-name chained-aws-lambda-fasttest-dev \
	  --enable-supervisortest --supervisortest-lambda-name chained-aws-lambda-supervisortest-dev \
	  --$*-policy-path chained-aws-lambda-$*/.chalice/policy.json --$*-app-path chained-aws-lambda-$*/app.py

	cat chained-aws-lambda/.chalice/config.json | jq '.app_name="chained-aws-lambda-$*"' > chained-aws-lambda-$*/.chalice/config.json
	# blindly enable access to our test S3 bucket.  This is ok since most daemons require it anyway.
	cat chained-aws-lambda-$*/.chalice/policy.json | jq -f s3_enable.filter | sponge chained-aws-lambda-$*/.chalice/policy.json
	cp -R ../src/chainedawslambda chained-aws-lambda-$*/domovoilib
	./build_deploy_config.sh chained-aws-lambda-$* dev

.PHONY: chained-aws-lambda $(chainedawslambdatargets) $(chainedawslambdaconfigtargets)

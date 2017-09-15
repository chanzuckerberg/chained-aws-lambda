include ../common.mk

deploy: dss-chunked-task

awschunkedtasktargets := $(shell ../scripts/get_all_dss_chunked_task_clients.py)
dss-chunked-task: $(awschunkedtasktargets)
$(awschunkedtasktargets): dss-chunked-task-%:
	rm -rf $@
	cp -rf dss-chunked-task $@
	cat dss-chunked-task/.chalice/config.json | jq '.app_name="$@" | .stages.$(DEPLOYMENT_STAGE).environment_variables.CHUNKED_TASK_CLIENT_NAME="$*"' > $@/.chalice/config.json
	cp -R ../dss $@/domovoilib
	./build_deploy_config.sh $@ $(DEPLOYMENT_STAGE)
	cd $@; CHUNKED_TASK_CLIENT_NAME=$* domovoi deploy --stage $(DEPLOYMENT_STAGE)

.PHONY: dss-chunked-task $(awschunkedtasktargets)

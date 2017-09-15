include ../common.mk

deploy: dss-chunked-task

awschunkedtasktargets := $(shell ../scripts/get_all_dss_chunked_task_clients.py)
dss-chunked-task: $(awschunkedtasktargets)
$(awschunkedtasktargets): dss-chunked-task-%:
	rm -rf $@
	cp -rf dss-chunked-task $@
	cat dss-chunked-task/.chalice/config.json | jq '.app_name="$@" | .stages.$(DSS_DEPLOYMENT_STAGE).environment_variables.DSS_CHUNKED_TASK_CLIENT_NAME="$*"' > $@/.chalice/config.json
	shopt -s nullglob; for wheel in $@/vendor.in/*/*.whl; do unzip -q -o -d $@/vendor $$wheel; done
	cp -R ../dss ../dss-api.yml $@/domovoilib
	cp "$(GOOGLE_APPLICATION_CREDENTIALS)" $@/domovoilib/gcp-credentials.json
	./build_deploy_config.sh $@ $(DSS_DEPLOYMENT_STAGE)
	cd $@; DSS_CHUNKED_TASK_CLIENT_NAME=$* domovoi deploy --stage $(DSS_DEPLOYMENT_STAGE)

.PHONY: dss-chunked-task $(awschunkedtasktargets)

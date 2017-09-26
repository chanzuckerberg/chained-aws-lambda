include common.mk
MODULES=src/chainedawslambda tests

lint:
	flake8 $(MODULES) daemons/*/*.py

mypy:
	mypy --ignore-missing-imports $(MODULES)

test_srcs := $(wildcard tests/test_*.py)

test: lint mypy
	coverage run --source=src/chainedawslambda -m unittest discover tests -v

fast_test: lint mypy $(test_srcs)

$(test_srcs): %.py :
	python -m unittest $@

deploy:
	$(MAKE) -C daemons deploy

clean:
	git clean -Xdf daemons $(MODULES)
	git clean -df daemons/*/{chalicelib,domovoilib}
	git checkout daemons/*/.chalice/config.json

.PHONY: test lint mypy $(test_srcs)

# HCA DSS: The Human Cell Atlas Data Storage System

This repository contains design specs and prototypes for the
replicated data storage system (aka the "blue box") of
the [Human Cell Atlas](https://www.humancellatlas.org/).

See the [google drive folder](https://drive.google.com/open?id=0B-_4IWxXwazQbWE5YmtqUWx3RVE) for live collaborative documents.

#### About this prototype
The prototype in this repository uses [Swagger](http://swagger.io/) to specify the API in [dss-api.yml](dss-api.yml), and
[Connexion](https://github.com/zalando/connexion) to map the API specification to its implementation in Python.

You can use the
[Swagger Editor](http://editor.swagger.io/#/?import=https://raw.githubusercontent.com/HumanCellAtlas/data-store/master/dss-api.yml)
to review and edit the prototype API specification. When the prototype app is running, the Swagger spec is also available at
`/v1/swagger.json`.

#### Installing dependencies for the prototype
Run `pip install -r requirements.txt` in this directory.

#### Running the prototype
Run `./dss-api` in this directory.

#### Running tests
Run `make test` in this directory.

[![](https://img.shields.io/badge/slack-%23data--store-557EBF.svg)](https://humancellatlas.slack.com/messages/data-store/)
[![Build Status](https://travis-ci.org/HumanCellAtlas/data-store.svg?branch=master)](https://travis-ci.org/HumanCellAtlas/data-store)

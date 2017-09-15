# chained-aws-lambda

#### Running tests

Run `make test` in the top-level `data-store` directory.


#### Deployment

Assuming the tests have passed above, the next step is to manually deploy.  See the section below for information on
CI/CD with Travis if continuous deployment is your goal.

Now deploy using make:

    make deploy

Set up AWS API Gateway.  The gateway is automatically set up for you and associated with the Lambda.  However, to get a
friendly domain name, you need to follow the
directions [here](http://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html). In summary:

* Generate a HTTPS certificate via AWS Certificate Manager, make sure it's in us-east-1
* Set up the domain name in the API gateway console
* Set up in Amazon Route 53 to point the domain to the API gateway
* In the API Gateway, fill in the endpoints for the custom domain name e.g. Path=`/`, Destination=`dss` and `dev`.
  These might be different based on the profile used (dev, stage, etc).
* Set the environment variable `API_HOST` to your domain name in the `environment.local` file.

If successful, you should be able to see the Swagger API documentation at:

    https://<domain_name>

And you should be able to list bundles like this:

    curl -X GET "https://<domain_name>/v1/bundles" -H  "accept: application/json"


#### CI/CD with Travis CI
We use [Travis CI](https://travis-ci.org/HumanCellAtlas/data-store) for continuous integration testing and
deployment. When `make test` succeeds, Travis CI deploys the application into the `dev` stage on AWS for every commit
that goes on the master branch. This behavior is defined in the `deploy` section of `.travis.yml`.


#### Authorizing Travis CI to deploy
Encrypted environment variables give Travis CI the AWS credentials needed to run the tests and deploy the app. Run
`scripts/authorize_aws_deploy.sh IAM-PRINCIPAL-TYPE IAM-PRINCIPAL-NAME` (e.g. `authorize_aws_deploy.sh user hca-test`)
to give that principal the permissions needed to deploy the app. Because this is a limited set of permissions, it does
not have write access to IAM. To set up the IAM policies for resources in your account that the app will use, run `make
deploy` using privileged account credentials once from your workstation. After this is done, Travis CI will be able to
deploy on its own. You must repeat the `make deploy` step from a privileged account any time you change the IAM policies
in `policy.json.template` files.

[![](https://img.shields.io/badge/slack-%23data--store-557EBF.svg)](https://humancellatlas.slack.com/messages/data-store/)
[![Build Status](https://travis-ci.org/HumanCellAtlas/data-store.svg?branch=master)](https://travis-ci.org/HumanCellAtlas/data-store)
[![codecov](https://codecov.io/gh/HumanCellAtlas/data-store/branch/master/graph/badge.svg)](https://codecov.io/gh/HumanCellAtlas/data-store)

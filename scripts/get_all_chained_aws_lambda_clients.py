#!/usr/bin/env python

import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from dss.events.chainedawslambda import aws

for name in aws.get_clients().keys():
    print(f"chained-aws-lambda-{name}")

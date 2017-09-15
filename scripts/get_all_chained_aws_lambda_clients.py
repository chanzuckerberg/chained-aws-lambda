#!/usr/bin/env python

import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from chainedawslambda.events.chainedawslambda import aws

for name in aws.get_clients().keys():
    print(f"chained-aws-lambda-{name}")

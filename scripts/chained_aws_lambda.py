#!/usr/bin/env python

import argparse
import collections
import os
import sys

from jinja2 import FileSystemLoader, Environment

try:
    # if we're running this from a deployed setting, everything should be in the search path.  otherwise, fix up the
    # path and continue.
    import chainedawslambda
except ImportError:
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))  # noqa
    sys.path.insert(0, pkg_root)  # noqa

from chainedawslambda import _awstest, s3copyclient

PROVIDED_CLIENT_METADATA = {
    "S3 copy client": dict(
        description="executes a simple S3-S3 copy",
        argname="s3-copy",
        cls=s3copyclient.S3CopyTask,
    ),
    "S3 parallel copy client": dict(
        description="supervises a parallel S3-S3 copy",
        argname="s3-parallel-copy-supervisor",
        cls=s3copyclient.S3ParallelCopySupervisorTask,
        children=['S3 parallel copy worker'],
    ),
    "S3 parallel copy worker": dict(
        description="worker client for executing the parallel S3-S3 copy",
        argname="s3-parallel-copy-worker",
        cls=s3copyclient.S3ParallelCopyWorkerTask,
    ),
    "fast test": dict(
        description="counts from 0 to 5, serializing state on each count",
        argname="fasttest",
        cls=_awstest.AWSFastTestTask,
    ),
    "supervisor test": dict(
        description="client for testing supervisor code",
        argname="supervisortest",
        cls=_awstest.AWSSupervisorTask,
        children=['fast test'],
    ),
}


def parse_args():
    deps = collections.defaultdict(lambda: set())

    parser = argparse.ArgumentParser()

    parser.add_argument("account_id", help="AWS account ID for this deployment")
    lambda_action = parser.add_argument(
        "--lambda-name",
        help="The name of the lambda that manages this request.",
    )
    policy_path_action = parser.add_argument(
        "--policy-path",
        help="Write the minimum IAM policy for running this client to this file.",
    )
    app_path_action = parser.add_argument(
        "--app-path",
        help="Write the generated app.py to this file.",
    )
    children_action = parser.add_argument(
        "--child-lambda-name",
        help="List of lambdas this lambda might call.",
        type=str,
        action="append",
        dest="children_action",
        default=[],
    )

    deps[policy_path_action].add(lambda_action)
    deps[app_path_action].add(lambda_action)
    deps[children_action].add(policy_path_action)

    # add the arguments common to all groups.
    common_args = (
        ("lambda-name", str, "The name of the lambda that manages this request.", True),
        ("policy-path", str, "Write the minimum IAM policy for running this client to this file.", False),
        ("app-path", str, "Write the generated app.py to this file.", False)
    )

    groups = dict()
    for group_title, group_metadata in PROVIDED_CLIENT_METADATA.items():
        group = parser.add_argument_group(group_title, group_metadata['description'])
        enable_action = group.add_argument(f"--enable-{group_metadata['argname']}", action="store_true")
        group_metadata['dest'] = enable_action.dest
        group_metadata['arg_dests'] = dict()
        for common_arg_suffix, common_arg_type, common_arg_help, required in common_args:
            action = group.add_argument(
                f"--{group_metadata['argname']}-{common_arg_suffix}",
                type=common_arg_type,
                help=common_arg_help,
            )
            if required:
                deps[enable_action].add(action)
            group_metadata['arg_dests'][common_arg_suffix] = action.dest

        groups[group_title] = (group, group_metadata['argname'], enable_action)

    # map out any extra dependencies.
    for group_title, group_metadata in PROVIDED_CLIENT_METADATA.items():
        for child in group_metadata.get('children', []):
            deps[groups[group_title][2]].add(groups[child][2])

    args = parser.parse_args()

    # run some checks to ensure that everything is present.
    for enable_action, dep_action_list in deps.items():
        if getattr(args, enable_action.dest):
            # ensure that all the suffixes are set.
            for dep_action in dep_action_list:
                if not getattr(args, dep_action.dest):
                    parser.error(f"{dep_action.option_strings[0]} is required when "
                                 f"{enable_action.option_strings[0]} is specified")

    return args


def write_jinja_file(template_file, template_vars, file_path, overwrite=True):
    """
    Fill in a jinja template to specified file_path.

    :param template_file: The file name for the template.
    :param template_vars: A dictionary specifying any input variables to the template.
    :param file_path: The file path to write the completed function to.
    """
    mode = "w" if overwrite else "a"
    template_vars['give_header'] = overwrite

    dirname = os.path.dirname(__file__)

    template_loader = FileSystemLoader(
        searchpath=[
            os.path.join(dirname, "..", "templates"), # this is the non-installed path
            os.path.join(dirname, "..", "share", "chained-aws-lambda", "templates"),
        ])

    # An environment provides the data necessary to read and parse our templates. Pass in the loader object here.
    template_env = Environment(loader=template_loader, trim_blocks=True, lstrip_blocks=True)

    # Read the template file using the environment object.
    template = template_env.get_template(template_file)

    # Finally, process the template to produce our final text.
    output_text = template.render(template_vars)

    with open(file_path, mode) as f:
        f.write(output_text)


def main():
    args = parse_args()

    # build up a list of enabled provided clients.
    enabled_client_names = set(
        client_name
        for client_name, group_metadata in PROVIDED_CLIENT_METADATA.items()
        if getattr(args, group_metadata['dest'])
    )
    while True:
        added = set()
        for group in enabled_client_names:
            for child in PROVIDED_CLIENT_METADATA[group].get('children', []):
                added.add(child)

        before = len(enabled_client_names)
        enabled_client_names = enabled_client_names.union(added)
        after = len(enabled_client_names)
        if before == after:
            break

    # build up the directory of provided clients
    clients = list()
    for enabled_client_name in enabled_client_names:
        full_classname = str(PROVIDED_CLIENT_METADATA[enabled_client_name]['cls'])
        client = dict()
        client['package_name'], client['class_name'] = full_classname.rsplit(".", maxsplit=1)
        client['lambda_name'] = getattr(
            args,
            f"{PROVIDED_CLIENT_METADATA[enabled_client_name]['arg_dests']['lambda-name']}")

        clients.append(client)

    for enabled_client_name in enabled_client_names:
        dst_app_path = getattr(
            args,
            f"{PROVIDED_CLIENT_METADATA[enabled_client_name]['arg_dests']['app-path']}")
        policy_path = getattr(
            args,
            f"{PROVIDED_CLIENT_METADATA[enabled_client_name]['arg_dests']['policy-path']}")
        lambda_name = getattr(
            args,
            f"{PROVIDED_CLIENT_METADATA[enabled_client_name]['arg_dests']['lambda-name']}")
        children = PROVIDED_CLIENT_METADATA[enabled_client_name].get('children', [])
        children_lambda_names = [
            getattr(
                args,
                f"{PROVIDED_CLIENT_METADATA[child_client_name]['arg_dests']['lambda-name']}")
            for child_client_name in children
        ]
        if dst_app_path:
            write_jinja_file(
                "app.py.jinja",
                {
                    'provided_clients': clients,
                    'lambda_name': lambda_name,
                },
                dst_app_path,
            )
        if policy_path:
            write_jinja_file(
                "policy.json.jinja",
                {
                    'account_id': args.account_id,
                    'lambda_name': lambda_name,
                    'children_lambda': children_lambda_names,
                },
                policy_path,
            )

    if args.app_path:
        write_jinja_file(
            "app.py.jinja",
            {
                'provided_clients': clients,
                'lambda_name': args.lambda_name,
            },
            args.app_path,
        )
    if args.policy_path:
        write_jinja_file(
            "policy.json.jinja",
            {
                'account_id': args.account_id,
                'lambda_name': args.lambda_name,
                'children_lambda': args.children_action,
            },
            args.policy_path,
        )


if __name__ == "__main__":
    main()

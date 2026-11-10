"""Generate a reviewed update to the existing Alignn host access template."""

import argparse
import json
from pathlib import Path


def allow_runtime_pull(template):
    resources = template["Resources"]
    boundary = resources["RuntimeBoundary"]["Properties"]
    runtime = resources["RuntimeRole"]["Properties"]
    if boundary["ManagedPolicyName"] != "AlignnHostRuntimeBoundary":
        raise ValueError("Expected the existing Alignn host boundary")
    if runtime["RoleName"] != "AlignnHostRuntime" or runtime["PermissionsBoundary"] != {
        "Ref": "RuntimeBoundary"
    }:
        raise ValueError("Expected the bounded Alignn host role")
    policies = runtime["Policies"]
    if len(policies) != 1:
        raise ValueError("Review the runtime inline policies before patching")
    statements = [
        {
            "Sid": "AlignnReleaseRegistryLogin",
            "Effect": "Allow",
            "Action": "ecr:GetAuthorizationToken",
            "Resource": "*",
            "Condition": {"StringEquals": {"aws:RequestedRegion": "ap-south-1"}},
        },
        {
            "Sid": "AlignnReleaseImagePull",
            "Effect": "Allow",
            "Action": ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:BatchCheckLayerAvailability"],
            "Resource": [
                {"Fn::Sub": f"arn:${{AWS::Partition}}:ecr:ap-south-1:${{AWS::AccountId}}:repository/alignn-{image}"}
                for image in ("api", "web")
            ],
        },
    ]
    for policy in (boundary["PolicyDocument"], policies[0]["PolicyDocument"]):
        existing = {entry.get("Sid"): entry for entry in policy["Statement"]}
        for statement in statements:
            old = existing.get(statement["Sid"])
            if old is None:
                policy["Statement"].append(statement)
            elif old != statement:
                raise ValueError(f"Unexpected existing statement: {statement['Sid']}")
    return template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("current_template", type=Path)
    parser.add_argument("updated_template", type=Path)
    args = parser.parse_args()
    if args.current_template.resolve() == args.updated_template.resolve():
        parser.error("Use a separate output path for review")
    template = json.loads(args.current_template.read_text())
    output = json.dumps(allow_runtime_pull(template), indent=2)
    with args.updated_template.open("x") as target:
        target.write(output + "\n")


if __name__ == "__main__":
    main()

"""Adopt a branch from a third party"""
import json
import os
import subprocess

import click

URL_RE = (
    "(?P<repo_root>https://github.com/(?P<owner>.+)/(?P<repo>.+))/tree/(?P<branch>.+)"
)


def command(cmd):
    print(cmd)
    assert os.system(cmd) == 0


def pr_to_branch(pr_number):
    """
    adopt-branch pr_number

    pr_number is a number like "553" or whatever.
    """
    result = subprocess.run(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--json",
            "url,headRepositoryOwner,headRepository,headRefName",
        ],
        capture_output=True,
        text=True,  # This is to ensure that the output from the subprocess is text
    )

    assert result.returncode == 0, f"gh command failed: {result.stderr}"

    pr_info = json.loads(result.stdout)

    owner = pr_info["headRepositoryOwner"]["login"]
    repo = pr_info["headRepository"]["name"]
    branch = pr_info["headRefName"]
    print(pr_info["headRepository"])
    repo_url = f"https://github.com/{owner}/{repo}"

    assert all((owner, repo, branch, repo_url)), (owner, repo, branch, repo_url)

    return owner, repo, branch, repo_url


@click.command()
@click.argument("pr_number", required=True)
def adopt_branch(pr_number):
    """
    adopt-branch pr_number

    pr_number is a number like "553" or whatever.
    """
    owner, repo, branch, repo_url = pr_to_branch(pr_number)
    assert all((owner, repo, branch, repo_url)), (owner, repo, branch, repo_url)
    print("Using", repo, branch)
    try:
        command(f"git remote show {owner} 2>/dev/null")
    except AssertionError:
        command(f"git remote add {owner} {repo_url}")
    command(f"git fetch {owner}")
    command(f"git checkout --track {owner}/{branch}")
    command("git push origin")
    command("gh pr create")


adopt_branch()

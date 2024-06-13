"""Adopt a branch from a third party"""
import json
import os
import subprocess
import typing

import click

URL_RE = (
    "(?P<repo_root>https://github.com/(?P<owner>.+)/(?P<repo>.+))/tree/(?P<branch>.+)"
)


class PRInfo(typing.NamedTuple):
    owner: str
    repo: str
    branch: str
    repo_url: str
    title: str
    body: str
    author: str


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
            "url,headRepositoryOwner,headRepository,headRefName,title,body,author",
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

    assert all((owner, repo, branch)), (owner, repo, branch)

    return PRInfo(
        owner,
        repo,
        branch,
        repo_url=f"https://github.com/{owner}/{repo}",
        title=pr_info["title"],
        body=pr_info["body"],
        author=pr_info["author"]["login"],
    )


@click.command()
@click.argument("pr_number", required=True)
def adopt_branch(pr_number):
    """
    adopt-branch pr_number

    pr_number is a number like "553" or whatever.
    """
    pr_info = pr_to_branch(pr_number)
    print("Using", pr_info.repo, pr_info.branch)
    try:
        command(f"git remote show {pr_info.owner} 2>/dev/null")
    except AssertionError:
        command(f"git remote add {pr_info.owner} {pr_info.repo_url}")
    command(f"git fetch {pr_info.owner}")
    command(f"git checkout --track {pr_info.owner}/{pr_info.branch}")
    command("git push origin --set-upstream")
    title = f"{pr_info.title} -- from @{pr_info.author}"
    body = f"Copied from #{pr_number} by @{pr_info.author}\n\n{pr_info.body}"
    subprocess.run(["gh", "pr", "create", "--title", title, "--body", body])


adopt_branch()

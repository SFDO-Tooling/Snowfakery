"""Adopt a branch from a third party"""
import os
import re

import click

URL_RE = (
    "(?P<repo_root>https://github.com/(?P<owner>.+)/(?P<repo>.+))/tree/(?P<branch>.+)"
)


def command(cmd):
    print(cmd)
    assert os.system(cmd) == 0


@click.command()
@click.argument("url", required=True)
def adopt_branch(url):
    """
    adopt-branch URL

    URL is a github:// URL to the branch on the fork"
    """
    url_match = re.match(URL_RE, url)
    assert url_match, f"{url} did not match {URL_RE}"
    owner, repo, branch = url_match["owner"], url_match["repo"], url_match["branch"]
    repo_url = url_match["repo_root"]
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

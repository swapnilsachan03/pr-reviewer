import json
import os
import sys

from github import Auth, Github

from ..core.github_source import build_pr_context
from ..core.pipeline import run_review

HANDLED = {"opened", "synchronize", "reopened", "ready_for_review"}


def get_github_client(token: str | None):
    if not token:
        raise RuntimeError("github_token is missing")

    auth = Auth.Token(token)
    return Github(auth=auth)


def get_pr_event():
    event_path = os.environ.get("GITHUB_EVENT_PATH")

    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH is missing")

    with open(event_path, "r", encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    token = os.environ.get("INPUT_GITHUB_TOKEN")
    repository_name = os.environ.get("GITHUB_REPOSITORY")

    if not repository_name:
        raise RuntimeError("Can not read GitHub repository")

    event = get_pr_event()

    pr = event.get("pull_request", {})
    pr_number = pr.get("number")

    if not pr:
        raise RuntimeError("This workflow event does not contain a PR")

    if event.get("action") not in HANDLED or pr.get("draft"):
        print("Nothing to review.")
        return 0

    gh = get_github_client(token)

    pr_context = build_pr_context(gh, repository_name, pr_number, token)
    run_review(gh, pr_context)

    return 0


if __name__ == "__main__":
    sys.exit(main())

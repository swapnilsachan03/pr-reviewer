import json
import os
import sys

from github import Auth, Github

from core.config import HANDLED_PR_STATES
from review.pipeline import run_review
from context.review_context import build_pr_context
from comments.publisher import publish_review


def get_github_client(token: str | None):
    if not token:
        raise RuntimeError("github_token is missing")

    auth = Auth.Token(token)
    return Github(auth=auth, per_page=100)


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
    event_pr = event.get("pull_request", {})

    if not event_pr:
        raise RuntimeError("This workflow event does not contain a PR")

    pr_number = event_pr.get("number")

    if event.get("action") not in HANDLED_PR_STATES or event_pr.get("draft"):
        print("Nothing to review.")
        return 0

    gh = get_github_client(token)

    try:
        pr_context = build_pr_context(
            gh, repository_name, pr_number, token, event_pr["head"]["sha"]
        )

        findings = run_review(gh, pr_context)

        result = publish_review(
            gh=gh,
            findings=findings,
            context=pr_context,
            locations={},
        )

        print(f"Review ID: {result.review_id}")
        print(f"Inline comments: {result.inline_comments_created}")
        print(f"Skipped duplicates: {result.inline_comments_skipped}")
        print(f"Summary-only findings: {result.summary_only_findings}")

    finally:
        gh.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())

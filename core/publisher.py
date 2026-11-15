from github import Github
from github.PullRequest import PullRequest

from core.config import FINGERPRINT_PATTERN
from core.errors import ReviewSkipped
from core.schema import Finding, DiffLocation, PublishResult
from core.review_context import PRContext

from core.comment_renderer import render_inline_comment, render_summary


def publish_review(
    gh: Github,
    findings: list[Finding],
    context: PRContext,
    locations: dict[str, DiffLocation],
) -> PublishResult:
    repo = gh.get_repo(context.repository)
    pr = repo.get_pull(context.pr_number)

    if pr.head.sha != context.head_sha:
        raise ReviewSkipped(
            f"Stale run: review start {context.head_sha[:7]}, PR head {pr.head.sha[:7]}"
        )

    seen_fingerprints = _get_existing_fingerprints(gh, pr)

    comments = []
    skipped = 0
    summary_only = 0

    for finding in findings:
        if finding.fingerprint in seen_fingerprints:
            skipped += 1
            continue

        location = locations.get(finding.fingerprint)

        # Finding cannot be attached to a valid diff location.

        if location is None:
            summary_only += 1
            continue

        comment = {
            "path": location.path,
            "line": location.line,
            "side": location.side,
            "body": render_inline_comment(finding),
        }

        # Add multi-line positioning when applicable.

        if location.start_line is not None:
            if location.start_side is None:
                raise ValueError(
                    "start_side is required when start_line is provided"
                )

            if location.start_line > location.line:
                raise ValueError("start_line must be <= line")

            comment["start_line"] = location.start_line
            comment["start_side"] = location.start_side

        comments.append(comment)
        seen_fingerprints.add(finding.fingerprint)

    review = pr.create_review(
        commit=repo.get_commit(context.head_sha),
        body=render_summary(findings),
        event="COMMENT",
        comments=comments,
    )

    return PublishResult(
        review_id=review.id,
        total_findings=len(findings),
        inline_comments_created=len(comments),
        inline_comments_skipped=skipped,
        summary_only_findings=summary_only,
    )


def _get_existing_fingerprints(gh: Github, pr: PullRequest) -> set[str]:
    fingerprints = set()

    for comment in pr.get_review_comments():
        if not comment.body:
            continue

        if comment.user.type != "Bot":
            continue

        match = FINGERPRINT_PATTERN.search(comment.body)

        if match:
            fingerprints.add(match.group(1))

    return fingerprints

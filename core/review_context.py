import requests

from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository

from .schema import ChangedFile, PRContext
from .errors import ReviewSkipped
from .config import MAX_CHANGED_LINES, MAX_FILES, MAX_DIFF_BYTES, MAX_FILE_BYTES


def build_pr_context(
    gh: Github,
    repo_name: str,
    pr_number: int,
    token: str | None,
    expected_head_sha: str,
) -> PRContext:
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    if pr.state != "open":
        raise ReviewSkipped(f"PR is {pr.state}")

    elif expected_head_sha and pr.head.sha != expected_head_sha:
        raise ReviewSkipped(
            f"Stale run: event {expected_head_sha[:7]}, PR head {pr.head.sha[:7]}"
        )

    check_size(pr)

    owner, name = repo_name.split("/", 1)

    base_sha = pr.base.sha
    head_sha = pr.head.sha

    files = fetch_changed_files(pr, repo, head_sha)
    diff = fetch_unified_diff(owner, name, pr_number, token)

    return PRContext(
        repository=repo_name,
        pr_number=pr_number,
        title=pr.title,
        description=pr.body or "",
        author=pr.user.login,
        labels=[label.name for label in pr.labels],
        state=pr.state,
        url=pr.html_url,
        base_branch=pr.base.ref,
        head_branch=pr.head.ref,
        base_sha=base_sha,
        head_sha=head_sha,
        diff=diff,
        files=files,
    )


def fetch_changed_files(
    pull: PullRequest, repo: Repository, head_sha: str
) -> list[ChangedFile]:
    files = []

    for file in pull.get_files():
        content: str | None = None
        content_fetch_error: str | None = None

        if (
            file.status != "removed" and file.patch
        ):  # no patch => binary or too large
            try:
                content = fetch_file_contents(repo, file.filename, head_sha)
            except Exception as exc:
                content = None
                content_fetch_error = str(exc)

        files.append(
            ChangedFile(
                path=file.filename,
                status=file.status,
                previous_path=file.previous_filename,
                additions=file.additions,
                deletions=file.deletions,
                changes=file.changes,
                patch=file.patch,
                content=content,
                content_fetch_error=content_fetch_error,
            )
        )

    return files


def fetch_file_contents(repo, file_name, head_sha):
    content = repo.get_contents(
        file_name,
        head_sha,
    )

    if isinstance(content, list):
        # Not source files: directories, source modules, or symlinks.
        return None

    elif content.size > MAX_FILE_BYTES:
        raise ValueError(f"{content.size} bytes exceeds {MAX_FILE_BYTES}")

    else:
        return content.decoded_content.decode(
            "utf-8",
            errors="replace",
        )


def fetch_unified_diff(
    owner: str, repo_name: str, pr_number: int, token: str | None
):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo_name}/pulls/{pr_number}"
    )

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.diff",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )

    if response.status_code == 406:
        raise ReviewSkipped("GitHub refused to serve the diff (too large)")

    response.raise_for_status()

    if len(response.content) > MAX_DIFF_BYTES:
        raise ReviewSkipped(
            f"PR diff is {len(response.content)} bytes (limit {MAX_DIFF_BYTES})"
        )

    return response.text


def check_size(pr: PullRequest) -> None:
    if pr.changed_files > MAX_FILES:
        raise ReviewSkipped(
            f"PR touches {pr.changed_files} files (limit {MAX_FILES})"
        )

    lines = pr.additions + pr.deletions

    if lines > MAX_CHANGED_LINES:
        raise ReviewSkipped(
            f"PR changes {lines} lines (limit {MAX_CHANGED_LINES})"
        )

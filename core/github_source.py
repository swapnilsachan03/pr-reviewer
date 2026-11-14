import requests

from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository

from .schema import ChangedFile, PRContext


def build_pr_context(
    gh: Github, repo_name: str, pr_number: int, token: str | None
) -> PRContext:
    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        owner, repo_name = repo_name.split("/", 1)

        base_sha = pr.base.sha
        head_sha = pr.head.sha

        files = fetch_changed_files(pr, repo, head_sha)
        diff = fetch_unified_diff(owner, repo_name, pr_number, token)

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

    finally:
        gh.close()


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

    response.raise_for_status()

    return response.text


def fetch_file_contents(repo, file_name, head_sha):
    content = repo.get_contents(
        file_name,
        ref=head_sha,
    )

    if isinstance(content, list):
        # Directories are not source files.
        return None
    else:
        return content.decoded_content.decode(
            "utf-8",
            errors="replace",
        )

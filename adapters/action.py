import json
import os
import requests

from github import Auth, Github


def get_github_client():
    token = os.environ.get("INPUT_GITHUB_TOKEN")

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


def fetch_pr_metadata(pull):
    return {
        "number": pull.number,
        "title": pull.title,
        "description": pull.body or "",
        "author": pull.user.login,
        "base_branch": pull.base.ref,
        "head_branch": pull.head.ref,
        "state": pull.state,
        "url": pull.html_url,
    }


def fetch_changed_files(pull):
    files = []

    for file in pull.get_files():
        files.append(
            {
                "path": file.filename,
                "status": file.status,
                "additions": file.additions,
                "deletions": file.deletions,
                "changes": file.changes,
                "patch": file.patch,
            }
        )

    return files


def fetch_file_contents(repo, files, head_sha):
    for file in files:
        if file["status"] == "removed":
            file["content_at_head"] = None
            continue

        try:
            content = repo.get_contents(
                file["path"],
                ref=head_sha,
            )

            if isinstance(content, list):
                # Directories are not source files.
                file["content_at_head"] = None
            else:
                file["content_at_head"] = content.decoded_content.decode(
                    "utf-8",
                    errors="replace",
                )

        # Log the failure rather than silently pretending
        # that the file was successfully retrieved.

        except Exception as exc:
            file["content_at_head"] = None
            file["content_fetch_error"] = str(exc)

    return files


def fetch_unified_diff(owner, repo_name, pr_number, token):
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


def build_review_context():
    repository_name = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["INPUT_GITHUB_TOKEN"]

    event = get_pr_event()

    pr_number = event.get("pull_request", {}).get("number")

    if not pr_number:
        raise RuntimeError("This workflow event does not contain a PR")

    owner, repo_name = repository_name.split("/", 1)

    github = get_github_client()

    try:
        repo = github.get_repo(repository_name)
        pull = repo.get_pull(pr_number)

        base_sha = pull.base.sha
        head_sha = pull.head.sha

        metadata = fetch_pr_metadata(pull)

        files = fetch_changed_files(pull)

        files = fetch_file_contents(
            repo,
            files,
            head_sha,
        )

        unified_diff = fetch_unified_diff(
            owner,
            repo_name,
            pr_number,
            token,
        )

        return {
            "repository": repository_name,
            "pr_number": pr_number,
            "metadata": metadata,
            "base_sha": base_sha,
            "head_sha": head_sha,
            "files": files,
            "unified_diff": unified_diff,
        }

    finally:
        github.close()


def main():
    review_context = build_review_context()

    # pass this context to core review system.
    #
    # review = run_review(review_context)
    # publish_review(review)

    print(
        f"Successfully collected PR #{review_context['pr_number']} "
        f"from {review_context['repository']}"
    )


if __name__ == "__main__":
    main()

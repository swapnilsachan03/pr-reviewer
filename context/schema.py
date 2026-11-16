from pydantic import BaseModel


class ChangedFile(BaseModel):
    path: str
    status: str  # added | modified | removed | renamed
    previous_path: str | None = None
    additions: int
    deletions: int
    changes: int
    patch: str | None = None  # None for binary or oversized diffs
    content: str | None = (
        None  # file at head SHA; None if removed/binary/too big
    )
    content_fetch_error: str | None


class PRContext(BaseModel):
    repository: str  # "owner/name"
    pr_number: int
    title: str
    description: str
    author: str
    labels: list[str]
    state: str
    url: str
    base_branch: str
    head_branch: str
    base_sha: str
    head_sha: str
    diff: str  # unified diff, parseable by unidiff
    files: list[ChangedFile]

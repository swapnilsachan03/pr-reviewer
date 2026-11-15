from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator

from core.enums import FindingCategory, FindingSeverity


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


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fingerprint: str = Field(min_length=1)
    rule_id: Optional[str] = None

    category: FindingCategory
    severity: FindingSeverity
    confidence: float = Field(ge=0.0, le=1.0)

    path: str = Field(min_length=1)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)

    title: str = Field(min_length=1)
    explanation: str = Field(min_length=1)

    suggested_replacement: Optional[str] = None
    evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_line_range(self):
        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")
        return self


class DiffLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)

    # Final line of the comment range.
    line: int = Field(ge=1)
    side: Literal["LEFT", "RIGHT"]

    # Optional beginning of a multi-line comment.
    start_line: int | None = Field(default=None, ge=1)
    start_side: Literal["LEFT", "RIGHT"] | None = None


class PublishResult(BaseModel):
    review_id: int
    total_findings: int
    inline_comments_created: int
    inline_comments_skipped: int
    summary_only_findings: int

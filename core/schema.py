from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator


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


class FindingCategory(str, Enum):
    QUALITY = "quality"
    READABILITY = "readability"
    CORRECTNESS = "correctness"
    BLAST_RADIUS = "blast_radius"
    GUIDELINE = "guideline"
    SECURITY = "security"


class FindingSeverity(str, Enum):
    SEVERE = "severe"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NIT = "nit"


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: FindingCategory
    severity: FindingSeverity
    confidence: float = Field(ge=0.0, le=1.0)

    path: str = Field(min_length=1)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)

    title: str = Field(min_length=1)
    explanation: str = Field(min_length=1)

    suggested_patch: Optional[str] = None
    evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_line_range(self):
        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")
        return self

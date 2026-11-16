from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


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

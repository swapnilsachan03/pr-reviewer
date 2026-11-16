from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator

from review.enums import FindingCategory, FindingSeverity


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

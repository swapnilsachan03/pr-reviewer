from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator


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

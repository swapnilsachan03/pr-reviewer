from enum import Enum


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

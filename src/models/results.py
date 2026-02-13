"""
Data models for validation results, issues, and scores.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


class Severity(Enum):
    """Issue severity levels."""
    ERROR = "error"          # Blocks validation
    WARNING = "warning"      # Reduces score
    INFO = "info"           # Informational only


@dataclass
class ValidationIssue:
    """A single validation issue (error, warning, or info)."""
    severity: Severity
    category: str                    # e.g., "naming", "required_fields"
    message: str                     # Human-readable description
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None  # Fix suggestion


@dataclass
class ValidationResult:
    """Result of validating a single component."""
    component_type: str              # "skill", "agent", etc.
    component_name: str
    component_path: str
    valid: bool                      # Overall pass/fail
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    scores: Optional[Dict[str, float]] = None  # Dimension scores

    @property
    def all_issues(self) -> List[ValidationIssue]:
        """Get all issues sorted by severity."""
        return self.errors + self.warnings + self.info

    @property
    def issue_count(self) -> Dict[str, int]:
        """Count issues by severity."""
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "info": len(self.info)
        }

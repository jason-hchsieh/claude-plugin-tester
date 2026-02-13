"""
Base validator class with shared utilities.
"""
from abc import ABC, abstractmethod
from typing import Dict, List
import re
from src.models.results import ValidationResult, ValidationIssue, Severity


class BaseValidator(ABC):
    """Base class for all component validators."""

    @abstractmethod
    def validate(self, component: dict, plugin_context: dict) -> ValidationResult:
        """
        Validate a plugin component.

        Args:
            component: Component data (parsed from file)
            plugin_context: Full plugin context for cross-component validation

        Returns:
            ValidationResult with errors, warnings, and scores
        """
        pass

    def _check_naming(self, name: str, file_path: str) -> List[ValidationIssue]:
        """
        Validate kebab-case naming convention.

        Rules:
        - 3-50 characters
        - Lowercase letters, numbers, hyphens only
        - Must start and end with alphanumeric
        - No reserved prefixes (claude-, anthropic-)
        """
        issues = []

        # Length check
        if len(name) < 3:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category="naming",
                message=f"Name '{name}' is too short (minimum 3 characters)",
                file_path=file_path,
                suggestion="Use a more descriptive name (3-50 characters)"
            ))

        if len(name) > 50:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category="naming",
                message=f"Name '{name}' is too long (maximum 50 characters)",
                file_path=file_path
            ))

        # Format check: kebab-case
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name):
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category="naming",
                message=f"Name '{name}' must be kebab-case (lowercase, hyphens only)",
                file_path=file_path,
                suggestion=f"Suggested: '{self._to_kebab_case(name)}'"
            ))

        # Reserved prefixes
        if name.startswith(('claude-', 'anthropic-')):
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category="naming",
                message=f"Name '{name}' uses reserved prefix (claude-, anthropic-)",
                file_path=file_path,
                suggestion="Choose a different name without reserved prefixes"
            ))

        return issues

    def _check_required_fields(self, data: dict, required: List[str], file_path: str) -> List[ValidationIssue]:
        """Check that required fields are present."""
        issues = []
        for field in required:
            if field not in data:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="required_fields",
                    message=f"Missing required field: '{field}'",
                    file_path=file_path,
                    suggestion=f"Add '{field}' field to frontmatter"
                ))
        return issues

    def _check_description_quality(self, description: str, file_path: str) -> tuple[int, List[ValidationIssue]]:
        """
        Analyze description quality.

        Returns:
            (score 0-100, list of issues)
        """
        issues = []
        score = 0

        # Length check
        if len(description) < 10:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category="description_quality",
                message="Description too short (minimum 10 characters)",
                file_path=file_path,
                suggestion="Expand description with what the component does and when to use it"
            ))
            return 0, issues

        if len(description) >= 100:
            score += 20
        elif len(description) >= 50:
            score += 10
        else:
            score += 5

        # Action statement check
        action_verbs = ["creates", "manages", "analyzes", "generates", "validates",
                        "converts", "processes", "monitors", "configures", "deploys",
                        "builds", "tests", "runs", "executes", "handles"]
        if any(verb in description.lower() for verb in action_verbs):
            score += 20
        else:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="description_quality",
                message="Description lacks clear action statement",
                file_path=file_path,
                suggestion="Start with what the component does (e.g., 'Manages...', 'Analyzes...')"
            ))

        # Trigger conditions check
        trigger_phrases = ["use when", "use this", "trigger", "ask to", "asks for",
                          "mentions", "says", "requests", "use for"]
        matches = sum(1 for phrase in trigger_phrases if phrase in description.lower())
        score += min(30, matches * 10)

        if matches == 0:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="description_quality",
                message="Description missing trigger conditions",
                file_path=file_path,
                suggestion="Add 'Use when...' with specific user phrases"
            ))

        # Quoted examples check
        quoted_count = len(re.findall(r'"[^"]{3,}"', description))
        score += min(20, quoted_count * 5)

        # Vagueness penalty
        vague_patterns = ["helps with", "does things", "general purpose", "various tasks", "stuff"]
        if any(vague in description.lower() for vague in vague_patterns):
            score -= 10
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="description_quality",
                message="Description contains vague language",
                file_path=file_path,
                suggestion="Be specific about what the component does"
            ))

        return max(0, min(100, score)), issues

    def _check_xml_injection(self, text: str, file_path: str) -> List[ValidationIssue]:
        """Check for XML angle brackets (security issue)."""
        issues = []
        if '<' in text or '>' in text:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category="security",
                message="XML angle brackets detected in frontmatter (security risk)",
                file_path=file_path,
                suggestion="Remove < and > characters from frontmatter"
            ))
        return issues

    @staticmethod
    def _to_kebab_case(text: str) -> str:
        """Convert text to kebab-case."""
        # Replace spaces and underscores with hyphens
        text = re.sub(r'[\s_]+', '-', text)
        # Remove non-alphanumeric except hyphens
        text = re.sub(r'[^a-z0-9-]', '', text.lower())
        # Remove consecutive hyphens
        text = re.sub(r'-+', '-', text)
        # Remove leading/trailing hyphens
        text = text.strip('-')
        return text

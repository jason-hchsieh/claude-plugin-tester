"""
Skills Validator

Validates skill files (SKILL.md) against validation rules.
"""
from typing import Dict
from pathlib import Path
from .base import BaseValidator
from src.models.results import ValidationResult, ValidationIssue, Severity


class SkillValidator(BaseValidator):
    """Validator for skill components."""

    def validate(self, component: dict, plugin_context: dict) -> ValidationResult:
        """
        Validate a skill component.

        Args:
            component: Dict with keys:
                - file_path: Path to SKILL.md
                - frontmatter: Parsed YAML frontmatter
                - body: Markdown body content
                - folder_name: Name of skill folder
            plugin_context: Full plugin context

        Returns:
            ValidationResult
        """
        file_path = component.get("file_path", "unknown")
        frontmatter = component.get("frontmatter", {})
        body = component.get("body", "")
        folder_name = component.get("folder_name", "")

        errors = []
        warnings = []
        info_issues = []

        # 1. Required fields check
        required_fields = ["name", "description"]
        errors.extend(self._check_required_fields(frontmatter, required_fields, file_path))

        # If missing required fields, can't continue validation
        if any(e.category == "required_fields" for e in errors):
            return ValidationResult(
                component_type="skill",
                component_name=frontmatter.get("name", "unknown"),
                component_path=file_path,
                valid=False,
                errors=errors,
                warnings=warnings,
                info=info_issues
            )

        name = frontmatter["name"]
        description = frontmatter["description"]

        # 2. Naming convention check
        naming_issues = self._check_naming(name, file_path)
        errors.extend([i for i in naming_issues if i.severity == Severity.ERROR])
        warnings.extend([i for i in naming_issues if i.severity == Severity.WARNING])

        # 3. File path check (must be SKILL.md, case-sensitive)
        if not file_path.endswith("/SKILL.md"):
            errors.append(ValidationIssue(
                severity=Severity.ERROR,
                category="file_organization",
                message="Skill file must be named 'SKILL.md' (exact case)",
                file_path=file_path,
                suggestion="Rename to SKILL.md"
            ))

        # 4. Folder name match check
        if folder_name and folder_name != name:
            warnings.append(ValidationIssue(
                severity=Severity.WARNING,
                category="file_organization",
                message=f"Folder name '{folder_name}' doesn't match skill name '{name}'",
                file_path=file_path,
                suggestion=f"Rename folder to '{name}'"
            ))

        # 5. Description quality check
        desc_score, desc_issues = self._check_description_quality(description, file_path)
        errors.extend([i for i in desc_issues if i.severity == Severity.ERROR])
        warnings.extend([i for i in desc_issues if i.severity == Severity.WARNING])

        # 6. Security check (XML injection)
        xml_issues = self._check_xml_injection(description, file_path)
        errors.extend(xml_issues)

        # 7. Description length check (schema compliance)
        if len(description) > 1024:
            errors.append(ValidationIssue(
                severity=Severity.ERROR,
                category="schema_compliance",
                message=f"Description too long ({len(description)} characters, max 1024)",
                file_path=file_path,
                suggestion="Shorten description or move details to SKILL.md body"
            ))

        # Calculate scores
        structural_score = self._calculate_structural_score(errors, warnings)
        functional_score = desc_score  # Simplified for demo
        documentation_score = self._calculate_documentation_score(body)

        scores = {
            "structural": structural_score,
            "functional": functional_score,
            "documentation": documentation_score
        }

        # Determine overall validity
        valid = len(errors) == 0

        return ValidationResult(
            component_type="skill",
            component_name=name,
            component_path=file_path,
            valid=valid,
            errors=errors,
            warnings=warnings,
            info=info_issues,
            scores=scores
        )

    def _calculate_structural_score(self, errors: list, warnings: list) -> float:
        """Calculate structural correctness score."""
        # Start at 100, deduct for issues
        score = 100.0
        score -= len(errors) * 15  # 15 points per error
        score -= len(warnings) * 5  # 5 points per warning
        return max(0.0, score)

    def _calculate_documentation_score(self, body: str) -> float:
        """Calculate documentation completeness score."""
        score = 0.0

        # Length check
        word_count = len(body.split())
        if 500 <= word_count <= 5000:
            score += 30
        elif 200 <= word_count < 500:
            score += 20
        elif word_count < 200:
            score += 10

        # Has examples section
        if "## Example" in body or "## examples" in body.lower():
            score += 25

        # Has headings
        heading_count = body.count("##")
        if heading_count >= 3:
            score += 20
        elif heading_count >= 1:
            score += 10

        # Has code blocks
        if "```" in body:
            score += 15

        return min(100.0, score)

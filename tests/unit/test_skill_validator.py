"""
Unit tests for Skills Validator

Tests follow TDD: Written before implementation to define expected behavior.
"""
import pytest
from pathlib import Path
from src.validators.skill_validator import SkillValidator
from src.models.results import ValidationResult, Severity


class TestSkillValidator:
    """Test suite for SkillValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return SkillValidator()

    @pytest.fixture
    def valid_skill_data(self):
        """Valid skill data for testing."""
        return {
            "file_path": "skills/my-skill/SKILL.md",
            "frontmatter": {
                "name": "my-skill",
                "description": "Manages database workflows. Use when user mentions 'database', 'SQL', or asks to 'optimize queries'."
            },
            "body": "# My Skill\n\nThis skill helps with database management.\n\n## Examples\n\nExample usage here.",
            "folder_name": "my-skill"
        }

    def test_validate_valid_skill_passes(self, validator, valid_skill_data):
        """Valid skill should pass validation."""
        result = validator.validate(valid_skill_data, {})

        assert result.valid == True
        assert len(result.errors) == 0

    def test_missing_name_field_fails(self, validator, valid_skill_data):
        """Skill without name field should fail."""
        del valid_skill_data["frontmatter"]["name"]

        result = validator.validate(valid_skill_data, {})

        assert result.valid == False
        assert any(e.category == "required_fields" for e in result.errors)

    def test_missing_description_fails(self, validator, valid_skill_data):
        """Skill without description should fail."""
        del valid_skill_data["frontmatter"]["description"]

        result = validator.validate(valid_skill_data, {})

        assert result.valid == False
        assert any(e.category == "required_fields" for e in result.errors)

    def test_invalid_naming_convention(self, validator, valid_skill_data):
        """Skill with invalid name format should fail."""
        valid_skill_data["frontmatter"]["name"] = "My_Skill"  # Underscores not allowed

        result = validator.validate(valid_skill_data, {})

        assert result.valid == False
        assert any(e.category == "naming" for e in result.errors)

    def test_name_too_short(self, validator, valid_skill_data):
        """Skill name < 3 characters should fail."""
        valid_skill_data["frontmatter"]["name"] = "ab"

        result = validator.validate(valid_skill_data, {})

        assert result.valid == False
        assert any(e.category == "naming" for e in result.errors)

    def test_reserved_name_prefix(self, validator, valid_skill_data):
        """Skill with reserved 'claude-' prefix should fail."""
        valid_skill_data["frontmatter"]["name"] = "claude-my-skill"

        result = validator.validate(valid_skill_data, {})

        assert result.valid == False
        assert any("reserved" in e.message.lower() for e in result.errors)

    def test_folder_name_mismatch(self, validator, valid_skill_data):
        """Skill folder name not matching frontmatter name should warn."""
        valid_skill_data["folder_name"] = "different-name"

        result = validator.validate(valid_skill_data, {})

        assert any(e.category == "file_organization" for e in result.warnings)

    def test_description_too_short(self, validator, valid_skill_data):
        """Description < 10 characters should fail."""
        valid_skill_data["frontmatter"]["description"] = "Too short"

        result = validator.validate(valid_skill_data, {})

        assert result.valid == False

    def test_vague_description_warning(self, validator, valid_skill_data):
        """Vague description should generate warning."""
        valid_skill_data["frontmatter"]["description"] = "Helps with stuff and things"

        result = validator.validate(valid_skill_data, {})

        assert any("vague" in e.message.lower() or "specific" in e.message.lower()
                   for e in result.warnings)

    def test_missing_trigger_phrases_warning(self, validator, valid_skill_data):
        """Description without trigger phrases should warn."""
        valid_skill_data["frontmatter"]["description"] = "This skill manages databases and queries."

        result = validator.validate(valid_skill_data, {})

        # Should warn about missing "Use when" or trigger phrases
        assert any("trigger" in e.message.lower() for e in result.warnings)

    def test_xml_brackets_security_fail(self, validator, valid_skill_data):
        """XML angle brackets in frontmatter should fail (security)."""
        valid_skill_data["frontmatter"]["description"] = "Manages <script>alert()</script> databases"

        result = validator.validate(valid_skill_data, {})

        assert result.valid == False
        assert any(e.category == "security" for e in result.errors)

    def test_scoring_calculation(self, validator, valid_skill_data):
        """Validator should calculate dimension scores."""
        result = validator.validate(valid_skill_data, {})

        assert result.scores is not None
        assert "structural" in result.scores
        assert "functional" in result.scores
        assert "documentation" in result.scores

        # Valid skill should score well
        assert result.scores["structural"] >= 80

    def test_filename_case_sensitive(self, validator, valid_skill_data):
        """File must be exactly 'SKILL.md' (case-sensitive)."""
        valid_skill_data["file_path"] = "skills/my-skill/skill.md"  # Wrong case

        result = validator.validate(valid_skill_data, {})

        assert any(e.category == "file_organization" for e in result.errors)

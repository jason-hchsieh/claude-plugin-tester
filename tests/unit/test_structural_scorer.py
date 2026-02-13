"""
Unit tests for Structural Scorer

Tests the structural correctness scoring engine that aggregates
validation results and calculates structural scores.
"""
import pytest
from src.scoring.structural_scorer import StructuralScorer
from src.models.results import ValidationResult, ValidationIssue, Severity


@pytest.fixture
def scorer():
    """Create a structural scorer instance."""
    return StructuralScorer()


@pytest.fixture
def perfect_validation_result():
    """Validation result with no issues."""
    return ValidationResult(
        component_type="skill",
        component_name="test-skill",
        component_path="/test/SKILL.md",
        valid=True,
        errors=[],
        warnings=[],
        info=[],
        scores={
            "structural": 100.0,
            "functional": 95.0,
            "documentation": 90.0
        }
    )


@pytest.fixture
def flawed_validation_result():
    """Validation result with multiple issues."""
    return ValidationResult(
        component_type="skill",
        component_name="flawed-skill",
        component_path="/test/skill.md",  # Wrong case
        valid=False,
        errors=[
            ValidationIssue(
                severity=Severity.ERROR,
                category="required_fields",
                message="Missing required field: description",
                file_path="/test/skill.md"
            ),
            ValidationIssue(
                severity=Severity.ERROR,
                category="schema_compliance",
                message="Description exceeds 1024 characters",
                file_path="/test/skill.md"
            )
        ],
        warnings=[
            ValidationIssue(
                severity=Severity.WARNING,
                category="file_organization",
                message="File should be named SKILL.md (case-sensitive)",
                file_path="/test/skill.md"
            )
        ],
        info=[],
        scores={
            "structural": 55.0,
            "functional": 70.0,
            "documentation": 60.0
        }
    )


class TestStructuralScorer:
    """Tests for StructuralScorer."""

    def test_score_perfect_plugin(self, scorer, perfect_validation_result):
        """Test scoring a plugin with perfect structural correctness."""
        results = [perfect_validation_result]

        score = scorer.score(results)

        assert score["overall_score"] == 100.0
        assert score["total_components"] == 1
        assert score["valid_components"] == 1
        assert len(score["breakdown_by_category"]) == 0  # No issues

    def test_score_empty_results(self, scorer):
        """Test scoring with no validation results."""
        results = []

        score = scorer.score(results)

        assert score["overall_score"] == 0.0
        assert score["total_components"] == 0
        assert score["valid_components"] == 0

    def test_score_flawed_plugin(self, scorer, flawed_validation_result):
        """Test scoring a plugin with structural issues."""
        results = [flawed_validation_result]

        score = scorer.score(results)

        # Should reflect the structural score from validation
        assert score["overall_score"] == 55.0
        assert score["total_components"] == 1
        assert score["valid_components"] == 0  # Has errors, not valid

        # Should have breakdown by category
        assert "required_fields" in score["breakdown_by_category"]
        assert "schema_compliance" in score["breakdown_by_category"]
        assert "file_organization" in score["breakdown_by_category"]

    def test_score_multiple_components(self, scorer, perfect_validation_result, flawed_validation_result):
        """Test scoring multiple components."""
        results = [perfect_validation_result, flawed_validation_result]

        score = scorer.score(results)

        # Average: (100 + 55) / 2 = 77.5
        assert score["overall_score"] == 77.5
        assert score["total_components"] == 2
        assert score["valid_components"] == 1

    def test_breakdown_by_category(self, scorer, flawed_validation_result):
        """Test that issues are properly categorized."""
        results = [flawed_validation_result]

        score = scorer.score(results)

        breakdown = score["breakdown_by_category"]

        # Check required_fields category
        assert breakdown["required_fields"]["count"] == 1
        assert breakdown["required_fields"]["severity"] == "error"

        # Check schema_compliance category
        assert breakdown["schema_compliance"]["count"] == 1
        assert breakdown["schema_compliance"]["severity"] == "error"

        # Check file_organization category
        assert breakdown["file_organization"]["count"] == 1
        assert breakdown["file_organization"]["severity"] == "warning"

    def test_breakdown_by_component_type(self, scorer):
        """Test scoring breakdown by component type."""
        skill_result = ValidationResult(
            component_type="skill",
            component_name="test-skill",
            component_path="/test/SKILL.md",
            valid=True,
            errors=[],
            warnings=[],
            scores={"structural": 100.0}
        )

        agent_result = ValidationResult(
            component_type="agent",
            component_name="test-agent",
            component_path="/test/agent.md",
            valid=True,
            errors=[],
            warnings=[],
            scores={"structural": 90.0}
        )

        results = [skill_result, agent_result]
        score = scorer.score(results)

        by_type = score["breakdown_by_type"]
        assert by_type["skill"]["count"] == 1
        assert by_type["skill"]["avg_score"] == 100.0
        assert by_type["agent"]["count"] == 1
        assert by_type["agent"]["avg_score"] == 90.0

    def test_issue_severity_weighting(self, scorer):
        """Test that errors impact score more than warnings."""
        result_with_error = ValidationResult(
            component_type="skill",
            component_name="skill-with-error",
            component_path="/test/skill1.md",
            valid=False,
            errors=[
                ValidationIssue(
                    severity=Severity.ERROR,
                    category="required_fields",
                    message="Missing field",
                    file_path="/test/skill1.md"
                )
            ],
            warnings=[],
            scores={"structural": 70.0}
        )

        result_with_warning = ValidationResult(
            component_type="skill",
            component_name="skill-with-warning",
            component_path="/test/skill2.md",
            valid=True,
            errors=[],
            warnings=[
                ValidationIssue(
                    severity=Severity.WARNING,
                    category="file_organization",
                    message="Minor issue",
                    file_path="/test/skill2.md"
                )
            ],
            scores={"structural": 95.0}
        )

        score1 = scorer.score([result_with_error])
        score2 = scorer.score([result_with_warning])

        # Error should result in lower score than warning
        assert score1["overall_score"] < score2["overall_score"]

    def test_score_with_missing_structural_score(self, scorer):
        """Test handling validation results without structural scores."""
        result = ValidationResult(
            component_type="skill",
            component_name="test-skill",
            component_path="/test/SKILL.md",
            valid=True,
            errors=[],
            warnings=[],
            scores={}  # No structural score
        )

        score = scorer.score([result])

        # Should calculate based on validity
        assert score["overall_score"] == 100.0  # Valid = 100

    def test_recommendations_generated(self, scorer, flawed_validation_result):
        """Test that recommendations are generated based on issues."""
        results = [flawed_validation_result]

        score = scorer.score(results)

        assert "recommendations" in score
        assert len(score["recommendations"]) > 0

        # Should have recommendations for each category with issues
        rec_categories = [rec["category"] for rec in score["recommendations"]]
        assert "required_fields" in rec_categories
        assert "schema_compliance" in rec_categories

    def test_score_summary_format(self, scorer, perfect_validation_result):
        """Test that score output has expected structure."""
        results = [perfect_validation_result]

        score = scorer.score(results)

        # Check required keys
        assert "overall_score" in score
        assert "total_components" in score
        assert "valid_components" in score
        assert "breakdown_by_category" in score
        assert "breakdown_by_type" in score
        assert "recommendations" in score

        # Check types
        assert isinstance(score["overall_score"], float)
        assert isinstance(score["total_components"], int)
        assert isinstance(score["valid_components"], int)
        assert isinstance(score["breakdown_by_category"], dict)
        assert isinstance(score["breakdown_by_type"], dict)
        assert isinstance(score["recommendations"], list)

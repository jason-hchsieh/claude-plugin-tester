"""
Structural Correctness Scorer

Aggregates validation results and calculates structural quality scores
based on the scoring framework defined in quality-framework.md.
"""
from typing import List, Dict, Any
from collections import defaultdict
from src.models.results import ValidationResult, ValidationIssue, Severity


class StructuralScorer:
    """
    Scores plugin structural correctness based on validation results.

    Implements the structural scoring dimension from the quality framework:
    - YAML/JSON Validity (20%)
    - Required Fields Present (25%)
    - Naming Conventions (20%)
    - File Organization (20%)
    - Schema Compliance (15%)
    """

    def score(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Calculate structural score from validation results.

        Args:
            validation_results: List of ValidationResult objects from validators

        Returns:
            Dict containing:
                - overall_score: float 0-100
                - total_components: int
                - valid_components: int
                - breakdown_by_category: dict of issue categories
                - breakdown_by_type: dict of scores by component type
                - recommendations: list of improvement suggestions
        """
        if not validation_results:
            return self._empty_score()

        # Aggregate structural scores
        structural_scores = []
        for result in validation_results:
            score = result.scores.get("structural", None) if result.scores else None
            if score is not None:
                structural_scores.append(score)
            else:
                # Fallback: 100 if valid, 0 if invalid
                structural_scores.append(100.0 if result.valid else 0.0)

        overall_score = sum(structural_scores) / len(structural_scores)

        # Count valid vs total
        valid_count = sum(1 for r in validation_results if r.valid)
        total_count = len(validation_results)

        # Breakdown by category
        category_breakdown = self._categorize_issues(validation_results)

        # Breakdown by component type
        type_breakdown = self._breakdown_by_type(validation_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(category_breakdown)

        return {
            "overall_score": overall_score,
            "total_components": total_count,
            "valid_components": valid_count,
            "breakdown_by_category": category_breakdown,
            "breakdown_by_type": type_breakdown,
            "recommendations": recommendations
        }

    def _empty_score(self) -> Dict[str, Any]:
        """Return empty score structure."""
        return {
            "overall_score": 0.0,
            "total_components": 0,
            "valid_components": 0,
            "breakdown_by_category": {},
            "breakdown_by_type": {},
            "recommendations": []
        }

    def _categorize_issues(self, results: List[ValidationResult]) -> Dict[str, Dict[str, Any]]:
        """
        Categorize all issues by category.

        Returns:
            Dict mapping category to {count, severity, examples}
        """
        category_data = defaultdict(lambda: {
            "count": 0,
            "severity": "info",
            "examples": []
        })

        for result in results:
            # Process errors
            for error in result.errors:
                cat = error.category
                category_data[cat]["count"] += 1
                category_data[cat]["severity"] = "error"
                category_data[cat]["examples"].append({
                    "message": error.message,
                    "file": error.file_path
                })

            # Process warnings
            for warning in result.warnings:
                cat = warning.category
                category_data[cat]["count"] += 1
                # Only upgrade severity if not already error
                if category_data[cat]["severity"] != "error":
                    category_data[cat]["severity"] = "warning"
                category_data[cat]["examples"].append({
                    "message": warning.message,
                    "file": warning.file_path
                })

            # Process info
            for info in result.info:
                cat = info.category
                category_data[cat]["count"] += 1
                # Keep existing severity if higher
                if category_data[cat]["severity"] not in ("error", "warning"):
                    category_data[cat]["severity"] = "info"
                category_data[cat]["examples"].append({
                    "message": info.message,
                    "file": info.file_path
                })

        # Limit examples to 3 per category
        for cat_info in category_data.values():
            cat_info["examples"] = cat_info["examples"][:3]

        return dict(category_data)

    def _breakdown_by_type(self, results: List[ValidationResult]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate score breakdown by component type.

        Returns:
            Dict mapping component_type to {count, avg_score, valid_count}
        """
        type_data = defaultdict(lambda: {
            "count": 0,
            "scores": [],
            "valid_count": 0
        })

        for result in results:
            comp_type = result.component_type
            type_data[comp_type]["count"] += 1

            # Get structural score
            score = result.scores.get("structural", None) if result.scores else None
            if score is not None:
                type_data[comp_type]["scores"].append(score)
            else:
                type_data[comp_type]["scores"].append(100.0 if result.valid else 0.0)

            if result.valid:
                type_data[comp_type]["valid_count"] += 1

        # Calculate averages
        breakdown = {}
        for comp_type, data in type_data.items():
            breakdown[comp_type] = {
                "count": data["count"],
                "avg_score": sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0.0,
                "valid_count": data["valid_count"]
            }

        return breakdown

    def _generate_recommendations(self, category_breakdown: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Generate actionable recommendations based on issues.

        Args:
            category_breakdown: Issue categorization from _categorize_issues

        Returns:
            List of recommendation dicts with category, severity, message
        """
        recommendations = []

        # Recommendation templates by category
        templates = {
            "required_fields": {
                "message": "Add missing required fields to component frontmatter",
                "priority": 1
            },
            "schema_compliance": {
                "message": "Fix schema violations (description length, field formats)",
                "priority": 1
            },
            "file_organization": {
                "message": "Rename files to match conventions (SKILL.md case-sensitive)",
                "priority": 2
            },
            "naming_convention": {
                "message": "Update component names to kebab-case (3-50 chars, lowercase)",
                "priority": 2
            },
            "yaml_validity": {
                "message": "Fix YAML/JSON parsing errors in frontmatter",
                "priority": 1
            }
        }

        # Generate recommendations for categories with errors/warnings
        for category, data in category_breakdown.items():
            if data["severity"] in ("error", "warning"):
                template = templates.get(category, {
                    "message": f"Address {category} issues",
                    "priority": 3
                })

                recommendations.append({
                    "category": category,
                    "severity": data["severity"],
                    "message": template["message"],
                    "affected_count": data["count"],
                    "priority": template["priority"]
                })

        # Sort by priority then severity
        severity_order = {"error": 0, "warning": 1, "info": 2}
        recommendations.sort(
            key=lambda r: (r["priority"], severity_order.get(r["severity"], 3))
        )

        return recommendations

"""
Unit tests for Test Runner

Tests the orchestration layer that discovers plugins, runs validators,
aggregates results, and generates quality scores.
"""
import pytest
from pathlib import Path
from src.runner import TestRunner
from src.models.results import ValidationResult, ValidationIssue, Severity


@pytest.fixture
def runner():
    """Create a test runner instance."""
    return TestRunner()


@pytest.fixture
def mock_plugin_path(tmp_path):
    """Create a minimal mock plugin structure."""
    plugin_dir = tmp_path / "test-plugin" / "0.1.0"
    plugin_dir.mkdir(parents=True)

    # Create a minimal SKILL.md
    skill_dir = plugin_dir / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)

    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("""---
name: test-skill
description: Use this skill when testing the framework
---

# Test Skill

This is a test skill.
""")

    return plugin_dir


class TestTestRunner:
    """Tests for TestRunner orchestration."""

    def test_runner_initialization(self, runner):
        """Test runner initializes with default config."""
        assert runner is not None
        assert hasattr(runner, "run")
        assert hasattr(runner, "discover_plugins")

    def test_discover_plugins_empty_directory(self, runner, tmp_path):
        """Test plugin discovery in empty directory."""
        plugins = runner.discover_plugins(str(tmp_path))

        assert isinstance(plugins, list)
        assert len(plugins) == 0

    def test_discover_plugins_finds_plugin(self, runner, mock_plugin_path):
        """Test plugin discovery finds valid plugin structure."""
        parent = mock_plugin_path.parent.parent
        plugins = runner.discover_plugins(str(parent))

        assert len(plugins) >= 1
        # Should find test-plugin
        plugin_names = [p["name"] for p in plugins]
        assert "test-plugin" in plugin_names

    def test_run_validation_on_plugin(self, runner, mock_plugin_path):
        """Test running validation on a single plugin."""
        parent = mock_plugin_path.parent.parent
        plugins = runner.discover_plugins(str(parent))

        result = runner.run(plugins[0])

        assert result is not None
        assert "plugin_name" in result
        assert "validation_results" in result
        assert "structural_score" in result

    def test_run_returns_validation_results(self, runner, mock_plugin_path):
        """Test that validation results are properly returned."""
        parent = mock_plugin_path.parent.parent
        plugins = runner.discover_plugins(str(parent))

        result = runner.run(plugins[0])

        validation_results = result["validation_results"]
        assert isinstance(validation_results, list)
        # Should have at least one result for the skill
        assert len(validation_results) > 0

    def test_run_calculates_structural_score(self, runner, mock_plugin_path):
        """Test that structural score is calculated."""
        parent = mock_plugin_path.parent.parent
        plugins = runner.discover_plugins(str(parent))

        result = runner.run(plugins[0])

        assert "structural_score" in result
        score_data = result["structural_score"]
        assert "overall_score" in score_data
        assert isinstance(score_data["overall_score"], (int, float))
        assert 0 <= score_data["overall_score"] <= 100

    def test_run_handles_invalid_plugin(self, runner, tmp_path):
        """Test runner handles invalid plugin gracefully."""
        # Create plugin with invalid structure
        invalid_plugin = tmp_path / "invalid" / "1.0.0"
        invalid_plugin.mkdir(parents=True)

        plugin_info = {
            "name": "invalid",
            "path": str(invalid_plugin)
        }

        result = runner.run(plugin_info)

        # Should return result even for invalid plugin
        assert result is not None
        assert "plugin_name" in result
        assert "validation_results" in result

    def test_run_multiple_plugins(self, runner, mock_plugin_path):
        """Test running validation on multiple plugins."""
        parent = mock_plugin_path.parent.parent
        plugins = runner.discover_plugins(str(parent))

        results = runner.run_all(plugins)

        assert isinstance(results, list)
        assert len(results) == len(plugins)

        # Each result should have required keys
        for result in results:
            assert "plugin_name" in result
            assert "validation_results" in result
            assert "structural_score" in result

    def test_progress_reporting(self, runner, mock_plugin_path):
        """Test that runner reports progress during execution."""
        parent = mock_plugin_path.parent.parent
        plugins = runner.discover_plugins(str(parent))

        # Capture progress callbacks
        progress_updates = []

        def progress_callback(current, total, plugin_name):
            progress_updates.append({
                "current": current,
                "total": total,
                "plugin": plugin_name
            })

        result = runner.run_all(plugins, progress_callback=progress_callback)

        # Should have received progress updates
        assert len(progress_updates) > 0
        # Last update should be complete
        assert progress_updates[-1]["current"] == progress_updates[-1]["total"]

    def test_error_handling_continues_on_failure(self, runner, tmp_path):
        """Test that runner continues even if one plugin fails."""
        # Create one good plugin and one bad plugin
        good_plugin = tmp_path / "good" / "1.0.0" / "skills" / "skill"
        good_plugin.mkdir(parents=True)
        (good_plugin / "SKILL.md").write_text("---\nname: good\ndescription: test\n---\nContent")

        bad_plugin = tmp_path / "bad" / "1.0.0" / "skills" / "skill"
        bad_plugin.mkdir(parents=True)
        # Invalid YAML
        (bad_plugin / "SKILL.md").write_text("---\ninvalid: yaml: structure:\n---\n")

        plugins = runner.discover_plugins(str(tmp_path))
        results = runner.run_all(plugins)

        # Should get results for both (even though one may have errors)
        assert len(results) == 2

    def test_filter_plugins_by_name(self, runner, mock_plugin_path):
        """Test filtering plugins by name pattern."""
        parent = mock_plugin_path.parent.parent

        # Discover with filter
        plugins = runner.discover_plugins(str(parent), name_filter="test-*")

        # Should only get plugins matching pattern
        for plugin in plugins:
            assert plugin["name"].startswith("test-")

    def test_result_aggregation(self, runner, mock_plugin_path):
        """Test that results are properly aggregated."""
        parent = mock_plugin_path.parent.parent
        plugins = runner.discover_plugins(str(parent))
        results = runner.run_all(plugins)

        summary = runner.aggregate_results(results)

        assert "total_plugins" in summary
        assert "total_components" in summary
        assert "avg_structural_score" in summary
        assert summary["total_plugins"] == len(plugins)

"""
Test Runner

Orchestrates plugin discovery, validation execution, and result aggregation.
Coordinates validators and scorers to produce comprehensive quality reports.
"""
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.validators.skill_validator import SkillValidator
from src.scoring.structural_scorer import StructuralScorer


class TestRunner:
    """
    Orchestrates plugin testing workflow:
    1. Plugin discovery
    2. Parallel validation execution
    3. Score calculation
    4. Result aggregation
    """

    def __init__(self, max_workers: int = 4):
        """
        Initialize test runner.

        Args:
            max_workers: Maximum parallel validator threads
        """
        self.max_workers = max_workers
        self.skill_validator = SkillValidator()
        self.structural_scorer = StructuralScorer()

    def discover_plugins(
        self,
        root_path: str,
        name_filter: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Discover plugins in directory structure.

        Expected structure:
            root_path/
                plugin-name/
                    version/
                        skills/
                        agents/
                        commands/
                        hooks/
                        plugin.json

        Args:
            root_path: Root directory to search (e.g., ~/.claude/plugins/cache/)
            name_filter: Optional glob pattern to filter plugin names

        Returns:
            List of plugin info dicts with name, version, path
        """
        root = Path(root_path)
        if not root.exists():
            return []

        plugins = []

        # Scan for plugin directories
        for plugin_dir in root.iterdir():
            if not plugin_dir.is_dir():
                continue

            plugin_name = plugin_dir.name

            # Apply name filter if provided
            if name_filter:
                import fnmatch
                if not fnmatch.fnmatch(plugin_name, name_filter):
                    continue

            # Find version directories
            for version_dir in plugin_dir.iterdir():
                if not version_dir.is_dir():
                    continue

                # Verify this looks like a plugin (has skills, agents, or plugin.json)
                has_components = any([
                    (version_dir / "skills").exists(),
                    (version_dir / "agents").exists(),
                    (version_dir / "plugin.json").exists()
                ])

                if has_components:
                    plugins.append({
                        "name": plugin_name,
                        "version": version_dir.name,
                        "path": str(version_dir)
                    })

        return plugins

    def run(self, plugin_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Run validation on a single plugin.

        Args:
            plugin_info: Dict with name, version, path

        Returns:
            Dict with plugin_name, validation_results, structural_score
        """
        plugin_name = plugin_info["name"]
        plugin_path = Path(plugin_info["path"])

        # Discover and validate components
        validation_results = []

        # Validate skills
        skills_dir = plugin_path / "skills"
        if skills_dir.exists():
            for skill_folder in skills_dir.iterdir():
                if not skill_folder.is_dir():
                    continue

                skill_file = skill_folder / "SKILL.md"
                if skill_file.exists():
                    # Parse skill file
                    try:
                        component = self._parse_skill_file(skill_file, skill_folder.name)
                        result = self.skill_validator.validate(component, {})
                        validation_results.append(result)
                    except Exception as e:
                        # Handle parsing errors gracefully
                        from src.models.results import ValidationResult, ValidationIssue, Severity
                        validation_results.append(
                            ValidationResult(
                                component_type="skill",
                                component_name=skill_folder.name,
                                component_path=str(skill_file),
                                valid=False,
                                errors=[ValidationIssue(
                                    severity=Severity.ERROR,
                                    category="parsing",
                                    message=f"Failed to parse skill file: {str(e)}",
                                    file_path=str(skill_file)
                                )]
                            )
                        )

        # Calculate structural score
        structural_score = self.structural_scorer.score(validation_results)

        return {
            "plugin_name": plugin_name,
            "plugin_version": plugin_info.get("version", "unknown"),
            "plugin_path": plugin_info["path"],
            "validation_results": validation_results,
            "structural_score": structural_score
        }

    def run_all(
        self,
        plugins: List[Dict[str, str]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run validation on multiple plugins in parallel.

        Args:
            plugins: List of plugin info dicts
            progress_callback: Optional callback(current, total, plugin_name)

        Returns:
            List of validation results (one per plugin)
        """
        results = []
        total = len(plugins)

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_plugin = {
                executor.submit(self.run, plugin): plugin
                for plugin in plugins
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_plugin):
                plugin = future_to_plugin[future]

                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Handle failures gracefully
                    results.append({
                        "plugin_name": plugin["name"],
                        "plugin_version": plugin.get("version", "unknown"),
                        "plugin_path": plugin["path"],
                        "error": str(e),
                        "validation_results": [],
                        "structural_score": self.structural_scorer.score([])
                    })

                completed += 1
                if progress_callback:
                    progress_callback(completed, total, plugin["name"])

        return results

    def aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results across multiple plugins.

        Args:
            results: List of plugin validation results

        Returns:
            Summary dict with aggregated metrics
        """
        total_plugins = len(results)
        total_components = sum(
            len(r.get("validation_results", []))
            for r in results
        )

        # Calculate average structural score
        structural_scores = [
            r["structural_score"]["overall_score"]
            for r in results
            if "structural_score" in r
        ]
        avg_structural_score = (
            sum(structural_scores) / len(structural_scores)
            if structural_scores else 0.0
        )

        # Count plugins with errors
        plugins_with_errors = sum(
            1 for r in results
            if any(
                not vr.valid
                for vr in r.get("validation_results", [])
            )
        )

        return {
            "total_plugins": total_plugins,
            "total_components": total_components,
            "avg_structural_score": avg_structural_score,
            "plugins_with_errors": plugins_with_errors,
            "plugins_clean": total_plugins - plugins_with_errors
        }

    def _parse_skill_file(self, skill_file: Path, folder_name: str) -> Dict[str, Any]:
        """
        Parse a SKILL.md file into component dict.

        Args:
            skill_file: Path to SKILL.md
            folder_name: Name of the skill folder

        Returns:
            Component dict with file_path, frontmatter, body, folder_name
        """
        content = skill_file.read_text(encoding="utf-8")

        # Split frontmatter and body
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1]
                body = parts[2].strip()

                # Parse YAML frontmatter
                frontmatter = yaml.safe_load(frontmatter_text) or {}

                return {
                    "file_path": str(skill_file),
                    "frontmatter": frontmatter,
                    "body": body,
                    "folder_name": folder_name
                }

        # No frontmatter found
        return {
            "file_path": str(skill_file),
            "frontmatter": {},
            "body": content,
            "folder_name": folder_name
        }

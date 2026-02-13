#!/usr/bin/env python3
"""
Command-line interface for Claude Plugin Tester.

Usage:
    claude-plugin-test discover --path ~/.claude/plugins/cache/
    claude-plugin-test validate --plugin my-plugin
    claude-plugin-test score --plugin my-plugin
    plugin-validate --plugin my-plugin
    plugin-score --plugin my-plugin
"""
import sys
import argparse
from pathlib import Path
from typing import Optional

from src.runner import TestRunner
from src.validators.skill_validator import SkillValidator
from src.scoring.structural_scorer import StructuralScorer


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Code Plugin Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover plugins
  claude-plugin-test discover --path ~/.claude/plugins/cache/

  # Validate specific plugin
  claude-plugin-test validate --plugin my-plugin --path ~/.claude/plugins/cache/

  # Run full test suite
  claude-plugin-test test --path ~/.claude/plugins/cache/

  # Score specific plugin
  claude-plugin-test score --plugin my-plugin --path ~/.claude/plugins/cache/
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Discover plugins")
    discover_parser.add_argument(
        "--path",
        default="~/.claude/plugins/cache/",
        help="Path to plugins directory (default: ~/.claude/plugins/cache/)"
    )
    discover_parser.add_argument(
        "--filter",
        help="Filter plugins by name pattern (glob)"
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate plugin")
    validate_parser.add_argument("--plugin", required=True, help="Plugin name")
    validate_parser.add_argument(
        "--path",
        default="~/.claude/plugins/cache/",
        help="Path to plugins directory"
    )

    # Test command (full suite)
    test_parser = subparsers.add_parser("test", help="Run full test suite")
    test_parser.add_argument(
        "--path",
        default="~/.claude/plugins/cache/",
        help="Path to plugins directory"
    )
    test_parser.add_argument(
        "--filter",
        help="Filter plugins by name pattern"
    )
    test_parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )

    # Score command
    score_parser = subparsers.add_parser("score", help="Score plugin quality")
    score_parser.add_argument("--plugin", required=True, help="Plugin name")
    score_parser.add_argument(
        "--path",
        default="~/.claude/plugins/cache/",
        help="Path to plugins directory"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    if args.command == "discover":
        return cmd_discover(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "test":
        return cmd_test(args)
    elif args.command == "score":
        return cmd_score(args)
    else:
        parser.print_help()
        return 1


def cmd_discover(args):
    """Discover plugins command."""
    print(f"Discovering plugins in: {args.path}")

    runner = TestRunner()
    plugins = runner.discover_plugins(
        str(Path(args.path).expanduser()),
        name_filter=args.filter
    )

    if not plugins:
        print("No plugins found.")
        return 1

    print(f"\nFound {len(plugins)} plugin(s):\n")
    for plugin in plugins:
        print(f"  • {plugin['name']} (v{plugin['version']})")
        print(f"    {plugin['path']}")

    return 0


def cmd_validate(args):
    """Validate plugin command."""
    print(f"Validating plugin: {args.plugin}")

    runner = TestRunner()
    plugins = runner.discover_plugins(
        str(Path(args.path).expanduser()),
        name_filter=args.plugin
    )

    if not plugins:
        print(f"Plugin '{args.plugin}' not found.")
        return 1

    plugin = plugins[0]
    result = runner.run(plugin)

    # Display results
    print(f"\n{'='*60}")
    print(f"Plugin: {result['plugin_name']} v{result['plugin_version']}")
    print(f"{'='*60}\n")

    validation_results = result["validation_results"]

    if not validation_results:
        print("No components found to validate.")
        return 1

    valid_count = sum(1 for r in validation_results if r.valid)
    total_count = len(validation_results)

    for vr in validation_results:
        status = "✓" if vr.valid else "✗"
        print(f"{status} {vr.component_type}: {vr.component_name}")

        if vr.errors:
            for error in vr.errors[:3]:  # Show first 3 errors
                print(f"  └─ ERROR: {error.message}")

        if vr.warnings:
            for warning in vr.warnings[:2]:  # Show first 2 warnings
                print(f"  └─ WARN: {warning.message}")

    print(f"\nValidation: {valid_count}/{total_count} components valid")

    return 0 if valid_count == total_count else 1


def cmd_test(args):
    """Run full test suite command."""
    print(f"Testing plugins in: {args.path}\n")

    runner = TestRunner(max_workers=args.workers)
    plugins = runner.discover_plugins(
        str(Path(args.path).expanduser()),
        name_filter=args.filter
    )

    if not plugins:
        print("No plugins found.")
        return 1

    print(f"Found {len(plugins)} plugin(s). Running tests...\n")

    # Progress callback
    def progress(current, total, plugin_name):
        print(f"[{current}/{total}] Testing {plugin_name}...")

    # Run all tests
    results = runner.run_all(plugins, progress_callback=progress)

    # Aggregate and display results
    summary = runner.aggregate_results(results)

    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"Total Plugins: {summary['total_plugins']}")
    print(f"Total Components: {summary['total_components']}")
    print(f"Average Score: {summary['avg_structural_score']:.1f}/100")
    print(f"Plugins Clean: {summary['plugins_clean']}")
    print(f"Plugins with Issues: {summary['plugins_with_errors']}")

    return 0 if summary['plugins_with_errors'] == 0 else 1


def cmd_score(args):
    """Score plugin quality command."""
    print(f"Scoring plugin: {args.plugin}")

    runner = TestRunner()
    plugins = runner.discover_plugins(
        str(Path(args.path).expanduser()),
        name_filter=args.plugin
    )

    if not plugins:
        print(f"Plugin '{args.plugin}' not found.")
        return 1

    plugin = plugins[0]
    result = runner.run(plugin)

    # Display score
    score = result["structural_score"]

    print(f"\n{'='*60}")
    print(f"Quality Score: {result['plugin_name']} v{result['plugin_version']}")
    print(f"{'='*60}\n")

    print(f"Overall Score: {score['overall_score']:.1f}/100")
    print(f"Components: {score['valid_components']}/{score['total_components']} valid\n")

    if score["breakdown_by_type"]:
        print("Breakdown by Type:")
        for comp_type, data in score["breakdown_by_type"].items():
            print(f"  • {comp_type}: {data['avg_score']:.1f}/100 ({data['count']} components)")

    if score["recommendations"]:
        print("\nRecommendations:")
        for rec in score["recommendations"][:5]:  # Show top 5
            print(f"  [{rec['severity'].upper()}] {rec['message']}")

    return 0


def validate():
    """Entry point for 'plugin-validate' command."""
    # Shortcut for validate command
    sys.argv.insert(1, "validate")
    return main()


def score():
    """Entry point for 'plugin-score' command."""
    # Shortcut for score command
    sys.argv.insert(1, "score")
    return main()


if __name__ == "__main__":
    sys.exit(main())

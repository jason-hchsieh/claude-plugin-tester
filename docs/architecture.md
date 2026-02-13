# Claude Code Plugin Testing Framework - Architecture

**Version:** 1.0
**Date:** 2026-02-13
**Status:** Design Complete

---

## Executive Summary

This document defines the architecture for a comprehensive testing and quality scoring framework for Claude Code plugins. The framework validates plugin structure, executes functional tests, scores quality across multiple dimensions, and generates actionable recommendations.

**Key Features:**
- Validates all 6 component types (skills, agents, commands, hooks, MCP configs, manifests)
- Executes user-authored tests (YAML, Python, Bash)
- Scores quality on 4 dimensions (structural, functional, code quality, documentation)
- Generates reports (JSON, Markdown, HTML dashboard)
- Integrates with existing tools (cc-plugin-eval, cclint, shellcheck)
- Target performance: <60s for medium plugins

---

## 1. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Entry Point                          │
│                    (test-plugin command)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Test Runner Orchestration                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Discover   │→ │   Validate   │→ │     Score    │→ Report │
│  │    Plugin    │  │  Components  │  │   Quality    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────────────────────────────────────────┘
         │                   │                   │
         │                   │                   │
         ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ Plugin         │  │ Validator      │  │ Scoring        │
│ Discovery      │  │ Layer          │  │ Engine         │
│                │  │                │  │                │
│ • Load plugin  │  │ • Skills       │  │ • Structural   │
│ • Parse files  │  │ • Agents       │  │ • Functional   │
│ • Build model  │  │ • Commands     │  │ • Code Quality │
│                │  │ • Hooks        │  │ • Documentation│
│                │  │ • MCP configs  │  │                │
│                │  │ • Manifest     │  │ • Composite    │
│                │  │                │  │   scorer       │
│                │  │ External:      │  │                │
│                │  │ • cclint       │  │ • Recommendation│
│                │  │ • cc-plugin-   │  │   engine       │
│                │  │   eval         │  │                │
│                │  │ • shellcheck   │  │                │
└────────────────┘  └────────────────┘  └────────────────┘
         │                   ║                   │
         │                   ║                   │
         ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ Plugin Model   │  │ Validation     │  │ Quality        │
│                │  │ Results        │  │ Scores         │
│ • Components   │  │                │  │                │
│ • Metadata     │  │ • Errors       │  │ • Dimension    │
│ • File paths   │  │ • Warnings     │  │   scores       │
│                │  │ • Info         │  │ • Overall      │
│                │  │ • Per-component│  │ • Grade band   │
│                │  │   scores       │  │ • Pass/fail    │
└────────────────┘  └────────────────┘  └────────────────┘
                             ║
                             ║ (parallel)
                             ▼
                    ┌────────────────┐
                    │ User Test      │
                    │ Execution      │
                    │                │
                    │ • Test Harness │
                    │   (Claude sim) │
                    │ • YAML Executor│
                    │ • Python Runner│
                    │ • Bash Runner  │
                    │ • Discovery    │
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ User Test      │
                    │ Results        │
                    │                │
                    │ • Pass/fail    │
                    │ • Severity     │
                    │ • Coverage     │
                    └────────────────┘
                             │
                             │ (merge)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Reporting Layer                             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ JSON Report  │  │ Markdown     │  │ HTML         │        │
│  │ (machine)    │  │ Report (CLI) │  │ Dashboard    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘

Legend:
  →  Sequential flow
  ║  Parallel execution
  ▼  Data transformation
```

---

## 2. Module Interface Definitions

### 2.1 Validator API

All validators implement this interface:

```python
from abc import ABC, abstractmethod
from typing import List
from models.results import ValidationResult, ValidationIssue, Severity

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

    def _parse_frontmatter(self, file_path: str) -> dict:
        """Shared utility: Parse YAML frontmatter from markdown."""
        pass

    def _check_naming(self, name: str) -> List[ValidationIssue]:
        """Shared utility: Validate kebab-case naming."""
        pass

    def _check_required_fields(self, data: dict, required: List[str]) -> List[ValidationIssue]:
        """Shared utility: Check required fields present."""
        pass
```

**ValidationResult Structure:**
```python
@dataclass
class ValidationResult:
    component_type: str           # "skill", "agent", "command", etc.
    component_name: str
    component_path: str
    valid: bool                   # Overall pass/fail
    errors: List[ValidationIssue] # Severity.ERROR
    warnings: List[ValidationIssue] # Severity.WARNING
    info: List[ValidationIssue]    # Severity.INFO
    scores: DimensionScores       # Structural, functional, etc.
```

**ValidationIssue Structure:**
```python
@dataclass
class ValidationIssue:
    severity: Severity            # ERROR, WARNING, INFO
    category: str                 # "naming", "required_fields", "security"
    message: str                  # Human-readable description
    file_path: str
    line_number: Optional[int]
    suggestion: Optional[str]     # Fix suggestion
```

### 2.2 Test Runner API

Central orchestrator:

```python
class TestRunner:
    """Orchestrates plugin validation, testing, scoring, and reporting."""

    def __init__(self, config: TestRunnerConfig):
        self.config = config
        self.validators = self._load_validators()
        self.scorers = self._load_scorers()
        self.test_executor = UserTestExecutor(config)

    def run(self, plugin_path: str) -> QualityReport:
        """
        Execute complete testing pipeline.

        Returns:
            QualityReport with all results, scores, and recommendations
        """
        plugin = self.discover_plugin(plugin_path)

        # Parallel execution
        validation_results = self.run_validators(plugin)
        user_test_results = self.test_executor.run_tests(plugin)

        # Scoring
        scores = self.compute_scores(validation_results, user_test_results)
        recommendations = self.generate_recommendations(scores, validation_results)

        # Report generation
        report = QualityReport(
            plugin=plugin,
            validation_results=validation_results,
            user_test_results=user_test_results,
            scores=scores,
            recommendations=recommendations,
            passed=self._determine_pass_fail(scores, validation_results)
        )

        return report

    def discover_plugin(self, path: str) -> Plugin:
        """Load and parse plugin from filesystem."""
        pass

    def run_validators(self, plugin: Plugin) -> Dict[str, ValidationResult]:
        """Run all validators in parallel, return results."""
        pass

    def compute_scores(self, validation_results, user_test_results) -> QualityScores:
        """Calculate quality scores across all dimensions."""
        pass
```

### 2.3 Scorer API

Each dimension has a scorer:

```python
class DimensionScorer(ABC):
    """Base class for dimension scorers."""

    @abstractmethod
    def score(self,
              validation_results: Dict[str, ValidationResult],
              user_test_results: Optional[UserTestResults],
              plugin: Plugin) -> DimensionScore:
        """
        Calculate score for this dimension.

        Returns:
            DimensionScore (0-100) with breakdown
        """
        pass
```

**DimensionScore Structure:**
```python
@dataclass
class DimensionScore:
    dimension: str                # "structural", "functional", etc.
    overall: float                # 0-100
    sub_scores: Dict[str, float]  # Sub-metric scores
    weight: float                 # Weight in overall score
    details: str                  # Explanation of score
```

### 2.4 User Test Execution API

```python
class UserTestExecutor:
    """Executes user-authored tests (YAML, Python, Bash)."""

    def run_tests(self, plugin: Plugin) -> UserTestResults:
        """
        Discover and execute all user tests.

        Returns:
            UserTestResults with pass/fail, coverage, severity
        """
        tests = self._discover_tests(plugin.path)

        results = []
        for test in tests:
            if test.format == "yaml":
                result = self.yaml_executor.run(test)
            elif test.format == "python":
                result = self.python_executor.run(test)
            elif test.format == "bash":
                result = self.bash_executor.run(test)
            results.append(result)

        return UserTestResults(
            total=len(results),
            passed=sum(1 for r in results if r.passed),
            failed=sum(1 for r in results if not r.passed),
            skipped=0,
            results=results,
            coverage=self._calculate_coverage(plugin, results)
        )
```

---

## 3. Data Flow

### 3.1 Complete Pipeline

```
Input: /path/to/plugin
  │
  ▼
┌────────────────────────────────────────────┐
│ 1. Plugin Discovery                        │
│                                            │
│ - Scan directory structure                 │
│ - Parse plugin.json                        │
│ - Discover components (glob skills/*/      │
│   SKILL.md, agents/*.md, etc.)             │
│ - Parse each component file                │
│ - Build Plugin object                      │
│                                            │
│ Output: Plugin {                           │
│   name, version, path,                     │
│   components: {                            │
│     skills: [...],                         │
│     agents: [...],                         │
│     ...                                    │
│   }                                        │
│ }                                          │
└────────────┬───────────────────────────────┘
             │
             ├───────────────────┬──────────────────────┐
             │                   │                      │
             ▼                   ▼                      ▼
┌────────────────────┐  ┌────────────────┐  ┌────────────────┐
│ 2A. Validation     │  │ 2B. User Test  │  │ 2C. External   │
│                    │  │ Execution      │  │ Validators     │
│ For each component:│  │                │  │                │
│ - Parse file       │  │ - Discover:    │  │ - cclint       │
│ - Check schema     │  │   tests/*.yaml │  │ - cc-plugin-   │
│ - Validate rules   │  │   tests/*.py   │  │   eval         │
│ - Calculate score  │  │   tests/*.sh   │  │ - shellcheck   │
│                    │  │                │  │                │
│ Output:            │  │ - Execute via  │  │ Call as        │
│ ValidationResult { │  │   test harness │  │ subprocesses,  │
│   valid: bool,     │  │                │  │ parse output   │
│   errors: [...],   │  │ - Aggregate    │  │                │
│   warnings: [...], │  │   results      │  │                │
│   scores: {...}    │  │                │  │                │
│ }                  │  │ Output:        │  │                │
│ per component      │  │ UserTestResults│  │                │
└────────────┬───────┘  └────────┬───────┘  └────────┬───────┘
             │                   │                    │
             └───────────────────┴────────────────────┘
                                 │
                                 ▼
             ┌───────────────────────────────────────┐
             │ 3. Scoring                            │
             │                                       │
             │ For each dimension:                   │
             │ - Aggregate validation results        │
             │ - Apply formulas from quality         │
             │   framework                           │
             │ - Integrate user test results         │
             │ - Calculate sub-scores                │
             │                                       │
             │ Composite Scorer:                     │
             │ - Apply dimension weights             │
             │ - Adjust for plugin complexity        │
             │ - Calculate overall score             │
             │ - Determine grade band                │
             │ - Assess pass/fail                    │
             │                                       │
             │ Output: QualityScores {               │
             │   overall: 85,                        │
             │   structural: 91,                     │
             │   functional: 78,                     │
             │   code_quality: 85,                   │
             │   documentation: 72,                  │
             │   grade: "B",                         │
             │   passed: true                        │
             │ }                                     │
             └─────────────┬─────────────────────────┘
                           │
                           ▼
             ┌───────────────────────────────────────┐
             │ 4. Recommendation Generation          │
             │                                       │
             │ For each low-scoring area:            │
             │ - Identify specific issues            │
             │ - Generate actionable fix             │
             │ - Prioritize (critical/high/med/low)  │
             │                                       │
             │ Output: Recommendation[] {            │
             │   priority: "high",                   │
             │   dimension: "functional",            │
             │   message: "Improve description...",  │
             │   details: [...]                      │
             │ }                                     │
             └─────────────┬─────────────────────────┘
                           │
                           ▼
             ┌───────────────────────────────────────┐
             │ 5. Report Generation                  │
             │                                       │
             │ Consolidate:                          │
             │ - Plugin metadata                     │
             │ - Validation results                  │
             │ - User test results                   │
             │ - Quality scores                      │
             │ - Recommendations                     │
             │                                       │
             │ Generate:                             │
             │ - JSON (machine-readable)             │
             │ - Markdown (CLI output)               │
             │ - HTML (dashboard)                    │
             │                                       │
             │ Output: QualityReport                 │
             └───────────────────────────────────────┘
                           │
                           ▼
                    [Output Files]
```

### 3.2 Error Handling Flow

```
Validation Error Detected
  │
  ├─ Critical (parse error, missing manifest)
  │  └─> Stop validation, return partial results
  │
  ├─ Error (missing required field, invalid schema)
  │  └─> Record error, continue validation, fail component
  │
  ├─ Warning (naming convention, missing optional field)
  │  └─> Record warning, continue validation, reduce score
  │
  └─ Info (best practice suggestion, optimization tip)
     └─> Record info, continue validation, neutral score impact
```

---

## 4. Technology Stack Decisions

### 4.1 Primary Language: **Python 3.8+**

**Rationale:**
- Rich ecosystem for YAML/JSON/Markdown parsing (PyYAML, jsonschema, python-markdown)
- Excellent regex and text processing (for description quality analysis)
- Good performance for I/O-bound tasks
- Easy integration with existing tools (subprocess for shellcheck, cclint)
- Type hints for maintainability (using dataclasses, typing module)
- Cross-platform compatibility

**Alternatives Considered:**
- Bash: Too limited for complex parsing, no structured data types
- Node.js: Good for JSON, but weaker YAML/Markdown ecosystem

### 4.2 Key Dependencies

```txt
# requirements.txt
pyyaml>=6.0              # YAML parsing
jsonschema>=4.17         # JSON schema validation
python-markdown>=3.4     # Markdown parsing
jinja2>=3.1              # HTML template rendering (dashboard)
click>=8.1               # CLI framework
pytest>=7.3              # Testing framework
pytest-cov>=4.0          # Code coverage
mypy>=1.0                # Type checking
black>=23.0              # Code formatting
pylint>=2.17             # Linting
```

### 4.3 Validator Implementation Strategy

**Hybrid Approach:**

1. **Leverage Existing Tools:**
   - **cclint** (npm): Structural validation via subprocess
     ```python
     subprocess.run(['npx', 'cclint', '--root', plugin_path, '--format', 'json'],
                    capture_output=True)
     ```
   - **cc-plugin-eval** (npm): Triggering validation via subprocess
     ```python
     subprocess.run(['npx', 'cc-plugin-eval', 'run', '-p', plugin_path, '--format', 'json'],
                    capture_output=True)
     ```
   - **shellcheck**: Hook script validation
     ```python
     subprocess.run(['shellcheck', script_path], capture_output=True)
     ```
   - **plugin-dev scripts**: Call validate-agent.sh, validate-hook-schema.sh

2. **Build Custom Validators:**
   - Description quality analysis (trigger phrase detection, vagueness checking)
   - Progressive disclosure pattern validation
   - Security pattern checking (quoted variables, input validation)
   - Component-specific rules not covered by existing tools

**Integration Pattern:**
```python
def validate_with_external_tool(tool_name, plugin_path):
    try:
        result = subprocess.run(
            [tool_command, *tool_args],
            capture_output=True,
            text=True,
            timeout=60
        )
        return parse_tool_output(result.stdout, tool_name)
    except subprocess.TimeoutExpired:
        return ToolResult(error="Tool timed out")
    except FileNotFoundError:
        return ToolResult(warning=f"{tool_name} not installed")
```

### 4.4 Test Harness: **Custom Python Simulator**

Simulate Claude Code environment for user tests:

```python
class ClaudeTestHarness:
    """Simulates Claude Code environment for testing."""

    def trigger_skill(self, skill_name, prompt):
        """Test if skill triggers on prompt."""
        # Load skill description
        # Match trigger phrases
        # Return triggered: bool

    def run_command(self, command_name, args):
        """Execute command in isolated environment."""
        # Set up CLAUDE_PLUGIN_ROOT
        # Execute command
        # Capture output
        # Return exit_code, stdout, stderr

    def invoke_agent(self, agent_name, task):
        """Simulate agent invocation."""
        # Mock agent execution
        # Return completion status
```

### 4.5 Dashboard: **Static HTML Generation**

```python
# Use Jinja2 templates + Bootstrap CSS
template = jinja2.Template(open('templates/dashboard.html').read())
html = template.render(
    plugin=plugin,
    scores=scores,
    recommendations=recommendations
)
```

**Why static:**
- No server required
- Fast generation
- Easy to email/share
- Works offline

**Dashboard Features:**
- Overall score gauge
- Dimension score radar chart
- Component breakdown table
- Recommendation cards with priority badges
- Test results summary
- Historical trend (if previous reports exist)

---

## 5. Integration with Existing Validators

### 5.1 cclint Integration

```python
class CclintIntegration:
    def validate(self, plugin_path: str) -> ValidationResult:
        cmd = ['npx', '@carlrannaberg/cclint',
               '--root', plugin_path,
               '--format', 'json']

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            # Parse JSON output
            data = json.loads(result.stdout)
            return self._convert_to_validation_result(data)
        else:
            return ValidationResult(
                errors=[ValidationIssue("cclint execution failed")]
            )

    def _convert_to_validation_result(self, cclint_output):
        # Map cclint issues to our ValidationIssue format
        pass
```

### 5.2 cc-plugin-eval Integration

```python
class CcPluginEvalIntegration:
    def validate_triggering(self, plugin_path: str) -> TriggerResults:
        cmd = ['npx', 'cc-plugin-eval', 'run',
               '-p', plugin_path,
               '--output', 'json']

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        data = json.loads(result.stdout)

        return TriggerResults(
            skills_triggered=data['skills'],
            agents_triggered=data['agents'],
            success_rate=data['success_rate']
        )
```

### 5.3 shellcheck Integration

```python
class ShellcheckIntegration:
    def validate_script(self, script_path: str) -> List[ValidationIssue]:
        cmd = ['shellcheck', '--format', 'json', script_path]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            return []  # No issues

        issues = json.loads(result.stdout)
        return [
            ValidationIssue(
                severity=self._map_severity(issue['level']),
                category='shell_script',
                message=issue['message'],
                file_path=script_path,
                line_number=issue['line']
            )
            for issue in issues
        ]
```

### 5.4 plugin-dev Scripts Integration

```python
class PluginDevScriptsIntegration:
    SCRIPTS_PATH = "~/.claude/plugins/cache/claude-plugins-official/plugin-dev"

    def validate_agent(self, agent_path: str) -> ValidationResult:
        script = f"{self.SCRIPTS_PATH}/skills/agent-development/scripts/validate-agent.sh"
        result = subprocess.run([script, agent_path],
                                 capture_output=True, text=True, timeout=10)
        return self._parse_script_output(result)

    def validate_hooks(self, hooks_json_path: str) -> ValidationResult:
        script = f"{self.SCRIPTS_PATH}/skills/hook-development/scripts/validate-hook-schema.sh"
        result = subprocess.run([script, hooks_json_path],
                                 capture_output=True, text=True, timeout=10)
        return self._parse_script_output(result)
```

---

## 6. Extensibility Considerations

### 6.1 Plugin-Based Validator System

Allow custom validators without modifying core:

```python
# Custom validator example
from framework.validators.base import BaseValidator

class MyCustomValidator(BaseValidator):
    component_type = "skill"  # Which component type this validates

    def validate(self, component, plugin_context):
        # Custom validation logic
        return ValidationResult(...)

# Register custom validator
TestRunner.register_validator(MyCustomValidator)
```

### 6.2 Configuration-Driven Scoring

Allow customization of scoring weights:

```yaml
# config/scoring-weights.yaml
dimensions:
  structural: 0.30
  functional: 0.30
  code_quality: 0.20
  documentation: 0.20

structural_sub_metrics:
  yaml_validity: 0.20
  required_fields: 0.25
  naming: 0.20
  file_organization: 0.20
  schema_compliance: 0.15
```

### 6.3 New Component Type Support

To add a new component type (e.g., "tools" in future Claude):

1. Create `src/validators/tool_validator.py`
2. Define validation rules in `config/validation-rules/tool-rules.yaml`
3. Register validator in `test_runner.py`
4. Add component discovery in `plugin_loader.py`

No core framework changes needed.

### 6.4 Custom Report Formats

Support additional report formats via plugins:

```python
class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, report: QualityReport) -> str:
        pass

class PDFReportGenerator(ReportGenerator):
    def generate(self, report):
        # Generate PDF using reportlab
        pass

# Register
TestRunner.register_report_format('pdf', PDFReportGenerator())
```

---

## 7. Performance & Scalability

### 7.1 Parallel Validation

**Strategy:** ThreadPoolExecutor for I/O-bound tasks

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_validators(self, plugin: Plugin) -> Dict[str, ValidationResult]:
    results = {}

    with ThreadPoolExecutor(max_workers=6) as executor:
        # Submit all validation tasks
        futures = {
            executor.submit(validator.validate, component, plugin): component_name
            for validator in self.validators
            for component_name, component in plugin.components.items()
        }

        # Collect results as they complete
        for future in as_completed(futures):
            component_name = futures[future]
            try:
                results[component_name] = future.result(timeout=60)
            except TimeoutError:
                results[component_name] = ValidationResult(
                    error="Validation timed out"
                )

    return results
```

**Parallel Tasks:**
- ✅ All component validators (skills, agents, commands, hooks, MCP, manifest) - independent
- ✅ External tool calls (cclint, cc-plugin-eval, shellcheck) - independent
- ✅ User test execution - tests can run in parallel
- ❌ Scoring - requires validation results (sequential after validation)

### 7.2 Caching Strategy

```python
class CachedValidator:
    def __init__(self, validator):
        self.validator = validator
        self.cache = {}

    def validate(self, component, plugin_context):
        # Cache key: (file_path, mtime)
        file_path = component['file_path']
        mtime = os.path.getmtime(file_path)
        cache_key = (file_path, mtime)

        if cache_key in self.cache:
            return self.cache[cache_key]  # Use cached result

        result = self.validator.validate(component, plugin_context)
        self.cache[cache_key] = result
        return result
```

**Cache Invalidation:**
- Invalidate on file modification time change
- Invalidate on framework version change
- Optional `--no-cache` flag for fresh validation

### 7.3 Incremental Validation

For large plugins or CI/CD integration:

```python
def validate_changed_components(plugin_path, base_commit='HEAD~1'):
    # Get changed files
    changed_files = subprocess.run(
        ['git', 'diff', '--name-only', base_commit],
        capture_output=True, text=True
    ).stdout.splitlines()

    # Filter to plugin files
    plugin_files = [f for f in changed_files if f.startswith(plugin_path)]

    # Map files to components
    changed_components = map_files_to_components(plugin_files)

    # Validate only changed components
    results = validate_components(changed_components)

    # Merge with previous results
    previous_results = load_previous_results()
    return merge_results(previous_results, results)
```

### 7.4 Large Plugin Optimization

For plugins with 1000+ skills:

- **Stream processing:** Process components one at a time instead of loading all into memory
- **Database backend:** Store validation results in SQLite for large plugin histories
- **Chunked reporting:** Generate partial reports during validation
- **Memory profiling:** Use `memory_profiler` to identify bottlenecks

**Target Performance:**
- Small plugin (1-5 components): <5 seconds
- Medium plugin (10-50 components): <60 seconds ✓
- Large plugin (100-500 components): <5 minutes
- Very large plugin (1000+ components): <30 minutes

---

## 8. Error Handling Strategy

### 8.1 Error Classification

```python
class FrameworkError(Exception):
    """Base class for framework errors."""
    pass

class PluginLoadError(FrameworkError):
    """Plugin cannot be loaded (missing manifest, corrupt files)."""
    pass

class ValidatorError(FrameworkError):
    """Validator failed to execute (not validation failure)."""
    pass

class ExternalToolError(FrameworkError):
    """External tool (cclint, shellcheck) failed."""
    pass

class TestExecutionError(FrameworkError):
    """User test execution failed (not test failure)."""
    pass
```

### 8.2 Graceful Degradation

```python
def run_validators_with_fallback(self, plugin):
    results = {}

    for validator_name, validator in self.validators.items():
        try:
            results[validator_name] = validator.validate(plugin)
        except ValidatorError as e:
            # Log error, continue with other validators
            logger.error(f"Validator {validator_name} failed: {e}")
            results[validator_name] = ValidationResult(
                valid=False,
                errors=[ValidationIssue(
                    severity=Severity.ERROR,
                    category="framework_error",
                    message=f"Validator failed: {e}"
                )]
            )

    # Proceed with partial results if at least 50% of validators succeeded
    success_rate = sum(1 for r in results.values() if r.valid) / len(results)
    if success_rate < 0.5:
        raise FrameworkError("Too many validator failures")

    return results
```

### 8.3 Error Reporting

```python
@dataclass
class ErrorReport:
    error_type: str
    message: str
    traceback: str
    context: dict
    suggestions: List[str]

def handle_error(error: Exception, context: dict) -> ErrorReport:
    """Convert exception to user-friendly error report."""

    if isinstance(error, PluginLoadError):
        return ErrorReport(
            error_type="Plugin Load Failed",
            message=str(error),
            traceback=traceback.format_exc(),
            context=context,
            suggestions=[
                "Check that plugin.json exists and is valid JSON",
                "Verify plugin directory structure",
                "Ensure all required files are present"
            ]
        )
    elif isinstance(error, ExternalToolError):
        return ErrorReport(
            error_type="External Tool Failed",
            message=str(error),
            traceback=traceback.format_exc(),
            context=context,
            suggestions=[
                "Install missing tool: npm install -g cclint",
                "Verify tool is in PATH",
                "Check tool version compatibility"
            ]
        )
    else:
        return ErrorReport(
            error_type="Unexpected Error",
            message=str(error),
            traceback=traceback.format_exc(),
            context=context,
            suggestions=[
                "Report this error as a bug",
                "Include full error details in report"
            ]
        )
```

---

## 9. Data Structures (JSON Schemas)

### 9.1 Plugin Object

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "path": "/path/to/plugin",
  "manifest": {
    "name": "my-plugin",
    "version": "1.0.0",
    "description": "Plugin description",
    "author": "Author Name"
  },
  "components": {
    "skills": [
      {
        "name": "my-skill",
        "path": "skills/my-skill/SKILL.md",
        "frontmatter": {
          "name": "my-skill",
          "description": "Skill description"
        },
        "body": "Skill content...",
        "references": ["references/guide.md"],
        "scripts": ["scripts/helper.py"]
      }
    ],
    "agents": [
      {
        "name": "my-agent",
        "path": "agents/my-agent.md",
        "frontmatter": {
          "name": "my-agent",
          "description": "Agent description with <example> blocks",
          "model": "sonnet",
          "color": "blue",
          "tools": ["Read", "Write"]
        },
        "system_prompt": "You are..."
      }
    ],
    "commands": [...],
    "hooks": {
      "path": "hooks/hooks.json",
      "config": {
        "hooks": {
          "PreToolUse": [...]
        }
      }
    },
    "mcp_configs": [...],
    "manifest_file": "plugin.json"
  }
}
```

### 9.2 ValidationResult

```json
{
  "component_type": "skill",
  "component_name": "my-skill",
  "component_path": "skills/my-skill/SKILL.md",
  "valid": true,
  "errors": [],
  "warnings": [
    {
      "severity": "warning",
      "category": "description_quality",
      "message": "Description could be more specific",
      "file_path": "skills/my-skill/SKILL.md",
      "line_number": 3,
      "suggestion": "Add trigger phrases like 'Use when...'"
    }
  ],
  "info": [],
  "scores": {
    "structural": 95,
    "functional": 75,
    "code_quality": null,
    "documentation": 80
  }
}
```

### 9.3 UserTestResults

```json
{
  "total": 15,
  "passed": 13,
  "failed": 2,
  "skipped": 0,
  "coverage": {
    "tested_components": 8,
    "total_components": 10,
    "percentage": 0.80
  },
  "results": [
    {
      "name": "Skill triggers on expected phrase",
      "format": "yaml",
      "component": "my-skill",
      "passed": true,
      "severity": "blocking",
      "duration_ms": 150
    },
    {
      "name": "Command handles invalid input",
      "format": "python",
      "component": "my-command",
      "passed": false,
      "severity": "warning",
      "error": "Expected exit code 1, got 0",
      "duration_ms": 250
    }
  ]
}
```

### 9.4 QualityScores

```json
{
  "overall": 85.3,
  "grade": "B+",
  "passed": true,
  "dimensions": {
    "structural": {
      "score": 91,
      "weight": 0.30,
      "sub_scores": {
        "yaml_validity": 100,
        "required_fields": 95,
        "naming": 90,
        "file_organization": 85,
        "schema_compliance": 85
      }
    },
    "functional": {
      "score": 78,
      "weight": 0.30,
      "sub_scores": {
        "description_quality": 75,
        "trigger_coverage": 80,
        "error_handling": 70,
        "user_tests": 87,
        "execution_readiness": 75
      }
    },
    "code_quality": {
      "score": 85,
      "weight": 0.20,
      "sub_scores": {
        "script_syntax": 100,
        "security": 80,
        "portability": 90,
        "best_practices": 75,
        "error_handling": 80
      }
    },
    "documentation": {
      "score": 72,
      "weight": 0.20,
      "sub_scores": {
        "description_body": 70,
        "examples": 65,
        "references": 80,
        "troubleshooting": 60,
        "clarity": 75
      }
    }
  },
  "component_scores": {
    "my-skill": 82,
    "my-agent": 88,
    "my-command": 79
  }
}
```

### 9.5 QualityReport

```json
{
  "plugin": { /* Plugin object */ },
  "validation_results": { /* ValidationResults per component */ },
  "user_test_results": { /* UserTestResults */ },
  "scores": { /* QualityScores */ },
  "recommendations": [
    {
      "priority": "high",
      "dimension": "functional",
      "message": "Improve description quality for skill 'my-skill'",
      "details": [
        "Add trigger phrases: include 'Use when...'",
        "Expand description: aim for 100+ characters"
      ]
    },
    {
      "priority": "medium",
      "dimension": "documentation",
      "message": "Add examples to command 'my-command'",
      "details": [
        "Include at least one usage example"
      ]
    }
  ],
  "passed": true,
  "timestamp": "2026-02-13T14:30:00Z",
  "framework_version": "1.0.0"
}
```

---

## 10. Directory Structure

```
claude-plugin-tester/
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── plugin.py              # Plugin data model
│   │   ├── results.py             # ValidationResult, UserTestResult
│   │   └── scores.py              # QualityScores, DimensionScore
│   │
│   ├── discovery/
│   │   ├── __init__.py
│   │   └── plugin_loader.py       # Plugin discovery and parsing
│   │
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── base.py                # BaseValidator ABC
│   │   ├── skill_validator.py     # Skills validator
│   │   ├── agent_validator.py     # Agents validator
│   │   ├── command_validator.py   # Commands validator
│   │   ├── hook_validator.py      # Hooks validator
│   │   ├── mcp_validator.py       # MCP configs validator
│   │   ├── manifest_validator.py  # plugin.json validator
│   │   └── integrations/
│   │       ├── cclint.py          # cclint integration
│   │       ├── cc_plugin_eval.py  # cc-plugin-eval integration
│   │       ├── shellcheck.py      # shellcheck integration
│   │       └── plugin_dev.py      # plugin-dev scripts integration
│   │
│   ├── harness/
│   │   ├── __init__.py
│   │   ├── claude_test_harness.py # Claude Code simulator
│   │   ├── yaml_executor.py       # YAML test executor
│   │   ├── python_executor.py     # Python test executor
│   │   └── bash_executor.py       # Bash test executor
│   │
│   ├── executors/
│   │   ├── __init__.py
│   │   ├── test_discovery.py      # User test discovery
│   │   └── test_executor.py       # User test execution orchestrator
│   │
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── structural_scorer.py   # Structural correctness scorer
│   │   ├── functional_scorer.py   # Functional effectiveness scorer
│   │   ├── code_quality_scorer.py # Code quality scorer
│   │   ├── documentation_scorer.py # Documentation scorer
│   │   ├── composite_scorer.py    # Composite scorer (overall)
│   │   └── recommendation_engine.py # Recommendation generator
│   │
│   ├── runner/
│   │   ├── __init__.py
│   │   └── test_runner.py         # Main orchestrator
│   │
│   └── reporting/
│       ├── __init__.py
│       ├── json_reporter.py       # JSON report generator
│       ├── markdown_reporter.py   # Markdown report generator
│       └── html_reporter.py       # HTML dashboard generator
│
├── tests/
│   ├── __init__.py
│   ├── fixtures/                  # Test plugin fixtures
│   │   ├── good-plugin/
│   │   ├── bad-plugin/
│   │   └── edge-case-plugin/
│   ├── unit/
│   │   ├── test_validators.py
│   │   ├── test_scorers.py
│   │   └── test_harness.py
│   ├── integration/
│   │   ├── test_full_pipeline.py
│   │   └── test_external_tools.py
│   └── conftest.py
│
├── config/
│   ├── scoring-weights.yaml       # Configurable scoring weights
│   └── validation-rules/          # Validation rule configurations
│       ├── skill-rules.yaml
│       ├── agent-rules.yaml
│       └── ...
│
├── templates/
│   ├── dashboard.html             # Jinja2 template for HTML dashboard
│   ├── markdown-report.md.j2      # Markdown report template
│   └── email-summary.html.j2      # Email-friendly summary
│
├── docs/
│   ├── architecture.md            # THIS FILE
│   ├── api-reference.md           # API documentation
│   ├── user-guide.md              # User documentation
│   ├── developer-guide.md         # For framework contributors
│   └── examples/
│       ├── custom-validator.md
│       └── custom-scorer.md
│
├── examples/
│   ├── good-plugin/               # Example well-scored plugin
│   ├── failing-plugin/            # Example low-scored plugin
│   └── edge-cases/                # Edge case examples
│
├── cli/
│   ├── __init__.py
│   └── main.py                    # Click CLI entry point
│
├── .mycelium/                     # Project context (gitignored)
│   ├── context/
│   │   ├── existing-tools.md
│   │   ├── validation-rules.md
│   │   ├── quality-framework.md
│   │   └── user-test-examples.md
│   ├── plans/
│   │   └── 2026-02-13-plugin-testing.md
│   └── state.json
│
├── .github/
│   └── workflows/
│       ├── test.yml               # CI: Run framework tests
│       └── validate-plugin.yml    # CI: Validate example plugins
│
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Development dependencies
├── setup.py                       # Package setup
├── pyproject.toml                 # Modern Python packaging
├── pytest.ini                     # Pytest configuration
├── mypy.ini                       # Type checking configuration
├── .pylintrc                      # Linting configuration
├── README.md                      # Project README
├── LICENSE                        # MIT License
└── CHANGELOG.md                   # Version history
```

---

## 11. Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Set up project structure
- [ ] Define data models (`models/`)
- [ ] Implement BaseValidator interface
- [ ] Plugin discovery and loading
- [ ] Basic test runner skeleton

### Phase 2: Validators (Week 2-3)
- [ ] Skill validator (reference implementation)
- [ ] Agent validator
- [ ] Command validator
- [ ] Hook validator
- [ ] MCP config validator
- [ ] Manifest validator
- [ ] External tool integrations

### Phase 3: User Testing (Week 3-4)
- [ ] Test harness (Claude simulator)
- [ ] YAML test executor
- [ ] Python test executor
- [ ] Bash test executor
- [ ] Test discovery engine

### Phase 4: Scoring (Week 4-5)
- [ ] Structural scorer
- [ ] Functional scorer
- [ ] Code quality scorer
- [ ] Documentation scorer
- [ ] Composite scorer
- [ ] Recommendation engine

### Phase 5: Reporting (Week 5)
- [ ] JSON reporter
- [ ] Markdown reporter
- [ ] HTML dashboard generator
- [ ] CLI interface

### Phase 6: Testing & Refinement (Week 6)
- [ ] Unit tests (>85% coverage)
- [ ] Integration tests
- [ ] Test against real plugins
- [ ] Performance optimization
- [ ] Documentation

---

## 12. Success Criteria

The architecture is successful when:

✅ **Modularity:**
- Each component has a single, well-defined responsibility
- Components are loosely coupled (interface-based)
- Easy to add new validators/scorers without touching core

✅ **Extensibility:**
- Plugin system for custom validators
- Configuration-driven scoring weights
- Support for future component types

✅ **Performance:**
- <60s execution for medium plugins (10-50 components)
- Parallel execution of independent validators
- Caching for repeated validations

✅ **Integration:**
- Seamlessly integrates with existing tools (cclint, cc-plugin-eval, shellcheck)
- Reuses existing validation logic where possible
- Adds value with custom validators

✅ **Usability:**
- Simple CLI interface
- Clear, actionable reports
- Beautiful HTML dashboard
- Helpful error messages

✅ **Maintainability:**
- Well-documented code with type hints
- Comprehensive test suite (>85% coverage)
- Clear architecture diagrams
- Easy to onboard new contributors

---

## 13. Open Questions & Future Considerations

### 13.1 CI/CD Integration
- GitHub Action for automatic plugin validation on PR?
- Badge generation for README (quality score badge)?
- Webhook integration for marketplace submissions?

### 13.2 Historical Tracking
- Store validation history in database?
- Trend charts showing quality over time?
- Regression detection (quality decreased)?

### 13.3 Marketplace Integration
- Auto-submit validated plugins to marketplace?
- Quality score displayed in marketplace?
- Minimum score required for marketplace acceptance?

### 13.4 Security Scanning
- Dedicated security scanner (beyond basic patterns)?
- Integration with vulnerability databases?
- Automated fix suggestions for security issues?

### 13.5 Performance Benchmarking
- Measure actual plugin performance (response time, token usage)?
- Load testing for hooks?
- Resource consumption analysis?

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-13 | Claude Sonnet 4.5 | Initial architecture design |

---

**End of Architecture Document**

This architecture provides a solid foundation for building a comprehensive, extensible, and maintainable testing framework for Claude Code plugins. Implementation can proceed with confidence in the design.

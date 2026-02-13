# Plugin Testing Framework - Implementation Guide

**Version:** 1.0
**Created:** 2026-02-13
**Status:** Strategic Implementation Complete (7/24 tasks done)

This guide provides comprehensive instructions for implementing the remaining 17 tasks in the plugin testing framework, building on the 3 reference implementations already completed.

---

## Table of Contents

1. [Overview](#overview)
2. [Reference Implementations](#reference-implementations)
3. [TDD Methodology](#tdd-methodology)
4. [Remaining Tasks by Priority](#remaining-tasks-by-priority)
5. [Implementation Instructions](#implementation-instructions)
6. [Testing Patterns](#testing-patterns)
7. [Integration Guidelines](#integration-guidelines)
8. [Common Pitfalls](#common-pitfalls)

---

## Overview

### What's Built (Reference Implementations)

Three production-ready modules demonstrating complete patterns:

1. **SkillValidator** (`src/validators/skill_validator.py`) - 164 lines, 13 tests
   - Validates skill components against rules
   - Demonstrates validation layer pattern
   - Shows scoring calculation
   - Handles errors gracefully

2. **StructuralScorer** (`src/scoring/structural_scorer.py`) - 235 lines, 10 tests
   - Aggregates validation results
   - Calculates quality scores
   - Generates recommendations
   - Demonstrates scoring pattern

3. **TestRunner** (`src/runner.py`) - 292 lines, 12 tests
   - Orchestrates discovery, validation, scoring
   - Parallel execution with ThreadPoolExecutor
   - Progress reporting
   - Demonstrates orchestration pattern

### What Remains (17 Tasks)

- **5 validators**: Agent, Command, Hook, MCP, Manifest (tasks 2.3-2.7)
- **6 user-test tasks**: Test harness, executors, discovery (tasks 2.8-2.13)
- **3 scorers**: Functional, code quality, composite (tasks 3.2-3.4)
- **1 integration**: Dashboard generator (task 4.2)
- **3 validation**: Real plugin testing, documentation, refinement (tasks 5.1-5.3)

---

## Reference Implementations

### 1. SkillValidator Pattern

**What it demonstrates:**
- Inherit from `BaseValidator` ABC
- Implement `validate(component, plugin_context)` method
- Use shared utilities from BaseValidator:
  - `_check_required_fields()`
  - `_check_naming()`
  - `_check_description_quality()`
  - `_check_xml_injection()`
- Calculate dimension scores (structural, functional, documentation)
- Return `ValidationResult` with errors/warnings/info/scores

**Key code structure:**
```python
class SkillValidator(BaseValidator):
    def validate(self, component: dict, plugin_context: dict) -> ValidationResult:
        # 1. Extract component data
        frontmatter = component.get("frontmatter", {})
        body = component.get("body", "")

        # 2. Check required fields (blocking)
        errors.extend(self._check_required_fields(...))
        if errors:
            return ValidationResult(valid=False, errors=errors)

        # 3. Run validation checks
        # - Naming conventions
        # - File organization
        # - Description quality
        # - Security (XML injection)
        # - Schema compliance

        # 4. Calculate scores
        scores = {
            "structural": structural_score,
            "functional": functional_score,
            "documentation": documentation_score
        }

        # 5. Return result
        return ValidationResult(
            component_type="skill",
            component_name=name,
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            scores=scores
        )
```

**Testing pattern:**
```python
class TestSkillValidator:
    def test_validate_valid_skill_passes(self):
        # Arrange: Create valid component data
        # Act: Call validator.validate()
        # Assert: result.valid == True, no errors

    def test_missing_required_field_fails(self):
        # Arrange: Create component missing field
        # Act: Call validator.validate()
        # Assert: result.valid == False, specific error present
```

### 2. StructuralScorer Pattern

**What it demonstrates:**
- Accept list of `ValidationResult` objects
- Aggregate scores across components
- Categorize issues by category and severity
- Break down results by component type
- Generate actionable recommendations

**Key code structure:**
```python
class StructuralScorer:
    def score(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        # 1. Extract structural scores from results
        structural_scores = [r.scores["structural"] for r in results]
        overall_score = sum(scores) / len(scores)

        # 2. Categorize issues
        category_breakdown = self._categorize_issues(results)

        # 3. Break down by type
        type_breakdown = self._breakdown_by_type(results)

        # 4. Generate recommendations
        recommendations = self._generate_recommendations(category_breakdown)

        # 5. Return comprehensive score dict
        return {
            "overall_score": overall_score,
            "total_components": len(results),
            "valid_components": count_valid,
            "breakdown_by_category": category_breakdown,
            "breakdown_by_type": type_breakdown,
            "recommendations": recommendations
        }
```

**Testing pattern:**
```python
def test_score_perfect_plugin(self, scorer, perfect_result):
    score = scorer.score([perfect_result])
    assert score["overall_score"] == 100.0

def test_score_flawed_plugin(self, scorer, flawed_result):
    score = scorer.score([flawed_result])
    assert score["overall_score"] < 100.0
    assert len(score["recommendations"]) > 0
```

### 3. TestRunner Pattern

**What it demonstrates:**
- Plugin discovery in filesystem
- Orchestrate multiple validators
- Parallel execution with ThreadPoolExecutor
- Progress callbacks
- Error handling and recovery
- Result aggregation

**Key code structure:**
```python
class TestRunner:
    def __init__(self, max_workers=4):
        self.skill_validator = SkillValidator()
        self.structural_scorer = StructuralScorer()

    def discover_plugins(self, root_path, name_filter=None):
        # Scan filesystem for plugin structure
        # Return list of plugin info dicts

    def run(self, plugin_info):
        # Run all validators on single plugin
        # Return validation results + scores

    def run_all(self, plugins, progress_callback=None):
        # Execute in parallel with ThreadPoolExecutor
        # Report progress via callback
        # Handle errors gracefully
```

---

## TDD Methodology

All implementations MUST follow this cycle:

### RED → GREEN → REFACTOR

#### 1. RED Phase: Write Failing Tests

```python
# Create tests/unit/test_<component>.py
# Write comprehensive tests that FAIL initially
pytest tests/unit/test_<component>.py  # Should fail (ModuleNotFoundError)
```

**What to test:**
- Valid inputs produce expected outputs
- Invalid inputs produce appropriate errors
- Edge cases handled correctly
- All public methods covered

#### 2. GREEN Phase: Minimal Implementation

```python
# Create src/<module>/<component>.py
# Write minimal code to make tests PASS
pytest tests/unit/test_<component>.py  # Should pass
```

**Implementation checklist:**
- Implement just enough to pass tests
- Don't add features not covered by tests
- Focus on correctness, not optimization

#### 3. REFACTOR Phase: Improve Code

```python
# Optional: Improve code quality
# - Extract functions
# - Remove duplication
# - Improve readability
pytest tests/unit/test_<component>.py  # Must still pass
```

#### 4. VERIFY Phase: Full Suite

```python
pytest tests/unit/ -v  # All tests must pass
```

#### 5. COMMIT Phase: Evidence-Based

```bash
git add <files>
git commit -m "Task X.Y: Component Name

RED: Created N tests, verified failures
GREEN: Implemented component, all tests pass
Evidence: X/X tests pass in Y.YYs

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Remaining Tasks by Priority

### Priority 1: Complete Validators (Tasks 2.3-2.7)

These are essential for comprehensive validation.

#### Task 2.3: Agent Validator
**Pattern:** Follow SkillValidator pattern
**Validation rules:** See `.mycelium/context/validation-rules.md` section "Agent Validation"
**Key differences from skills:**
- Required fields: name, description, model, color, tools
- Model validation (must be valid Claude model ID)
- Tool allowlist validation (check tools are valid)
- Color validation (must be valid CSS color)

**Implementation steps:**
1. Copy `test_skill_validator.py` → `test_agent_validator.py`
2. Modify fixtures for agent structure (frontmatter different from skills)
3. Add model/color/tools validation tests
4. Run tests (RED phase)
5. Copy `skill_validator.py` → `agent_validator.py`
6. Modify validation logic for agent-specific rules
7. Tests pass (GREEN phase)
8. Commit

**Estimated effort:** 2-3 hours

#### Task 2.4: Command Validator
**Pattern:** Follow SkillValidator pattern
**Key differences:**
- Validate command.json structure
- Check executable paths exist
- Validate environment variable usage
- Security: check for command injection risks

**Estimated effort:** 2-3 hours

#### Task 2.5: Hook Validator
**Pattern:** Follow SkillValidator pattern
**Key differences:**
- Validate hooks.json structure
- Check hook script files exist and are executable
- Validate event types (PreToolUse, PostToolUse, etc.)
- Security: check for shell injection in hook scripts

**Estimated effort:** 2-3 hours

#### Task 2.6: MCP Config Validator
**Pattern:** Follow SkillValidator pattern
**Key differences:**
- Validate mcp.json structure
- Check server binary exists
- Validate environment variables
- Check for proper error handling

**Estimated effort:** 2-3 hours

#### Task 2.7: Manifest Validator
**Pattern:** Follow SkillValidator pattern
**Key differences:**
- Validate plugin.json structure
- Check semver version format
- Validate required fields (name, version, description, author)
- Cross-reference with actual plugin structure

**Estimated effort:** 2-3 hours

### Priority 2: Complete Scorers (Tasks 3.2-3.4)

#### Task 3.2: Functional Effectiveness Scorer
**Pattern:** Follow StructuralScorer pattern
**Scoring formula:** See `.mycelium/context/quality-framework.md` section 1B
**Key metrics:**
- Description quality (trigger phrases, specificity)
- Error handling completeness
- User test pass rate (if tests exist)
- Component execution readiness

**Implementation approach:**
```python
class FunctionalScorer:
    def score(self, validation_results: List[ValidationResult]) -> Dict:
        # Extract functional scores from validation results
        # Calculate description quality metrics
        # Check error handling patterns
        # Return functional score 0-100
```

**Estimated effort:** 3-4 hours

#### Task 3.3: Code Quality Scorer
**Pattern:** Follow StructuralScorer pattern
**Integration:** Call external tools (shellcheck, pylint, etc.)
**Key metrics:**
- Script linting results
- Security scanning
- Code complexity
- Maintainability

**Estimated effort:** 3-4 hours

#### Task 3.4: Composite Scorer
**Pattern:** Aggregate all scorer outputs
**Formula:**
```
composite_score = (
    structural_score * 0.30 +
    functional_score * 0.30 +
    code_quality_score * 0.25 +
    documentation_score * 0.15
)
```

**Estimated effort:** 2 hours

### Priority 3: User-Authored Testing (Tasks 2.8-2.13)

These enable plugin developers to write their own tests.

#### Task 2.8: Design Test Manifest Format
**Deliverable:** JSON schema + examples
**Reference:** `.mycelium/context/user-test-examples.md`
**Estimated effort:** 2-3 hours

#### Task 2.9: Implement Test Harness
**Pattern:** Similar to TestRunner but for user tests
**Key features:**
- Simulate Claude Code environment
- Execute skill triggers
- Capture output and check assertions

**Estimated effort:** 6-8 hours (Large complexity)

#### Tasks 2.10-2.13: Test Executors & Discovery
**Pattern:** Extend test harness
**Estimated total effort:** 8-10 hours

### Priority 4: Integration & Validation (Tasks 4.2, 5.1-5.3)

#### Task 4.2: Quality Dashboard
**Pattern:** HTML generation from results
**Technology:** HTML + Tailwind CSS + Chart.js
**Estimated effort:** 4-5 hours

#### Tasks 5.1-5.3: Testing & Documentation
**Pattern:** Manual validation and documentation
**Estimated effort:** 4-6 hours

---

## Implementation Instructions

### For Each Validator (2.3-2.7)

**Step-by-step process:**

1. **Read validation rules**
   ```bash
   # See specific section in validation-rules.md
   cat .mycelium/context/validation-rules.md | grep -A 50 "Agent Validation"
   ```

2. **Create test file** (RED phase)
   ```bash
   cp tests/unit/test_skill_validator.py tests/unit/test_agent_validator.py
   # Modify for agent-specific tests
   pytest tests/unit/test_agent_validator.py  # Should fail
   ```

3. **Create validator** (GREEN phase)
   ```bash
   cp src/validators/skill_validator.py src/validators/agent_validator.py
   # Modify for agent-specific validation
   pytest tests/unit/test_agent_validator.py  # Should pass
   ```

4. **Integrate with TestRunner**
   ```python
   # In src/runner.py
   from src.validators.agent_validator import AgentValidator

   def __init__(self):
       self.skill_validator = SkillValidator()
       self.agent_validator = AgentValidator()  # Add

   def run(self, plugin_info):
       # ... existing skill validation ...

       # Add agent validation
       agents_dir = plugin_path / "agents"
       if agents_dir.exists():
           for agent_file in agents_dir.glob("**/*.md"):
               component = self._parse_agent_file(agent_file)
               result = self.agent_validator.validate(component, {})
               validation_results.append(result)
   ```

5. **Update tests**
   ```python
   # In tests/unit/test_runner.py
   # Add tests for agent discovery and validation
   ```

6. **Verify full suite**
   ```bash
   pytest tests/unit/ -v
   # All tests must pass
   ```

7. **Commit**
   ```bash
   git add src/validators/agent_validator.py tests/unit/test_agent_validator.py src/runner.py
   git commit -m "Task 2.3: Create Agent Validator Module"
   ```

### For Each Scorer (3.2-3.4)

**Follow the same pattern as StructuralScorer:**

1. **Study scoring formula** in `quality-framework.md`
2. **Write tests** defining expected scores
3. **Implement scorer** to make tests pass
4. **Integrate** into TestRunner or CompositeScorer
5. **Commit** with evidence

### For User Testing Framework (2.8-2.13)

**Higher complexity - plan carefully:**

1. **Task 2.8**: Design first (schema + examples)
2. **Task 2.9**: Build harness with basic execution
3. **Tasks 2.10-2.11**: Add test executors (YAML, Python, Bash)
4. **Task 2.12**: Discovery mechanism
5. **Task 2.13**: Integration with scoring

---

## Testing Patterns

### Test Structure Template

```python
"""
Unit tests for <Component>

<Brief description of what's being tested>
"""
import pytest
from src.<module>.<component> import <Component>
from src.models.results import ValidationResult, ValidationIssue, Severity


@pytest.fixture
def component():
    """Create component instance."""
    return <Component>()


@pytest.fixture
def valid_input():
    """Create valid test input."""
    return {
        # ... valid data ...
    }


@pytest.fixture
def invalid_input():
    """Create invalid test input."""
    return {
        # ... invalid data ...
    }


class Test<Component>:
    """Tests for <Component>."""

    def test_valid_input_passes(self, component, valid_input):
        """Test that valid input produces expected output."""
        result = component.process(valid_input)

        assert result is not None
        assert result.valid == True
        assert len(result.errors) == 0

    def test_invalid_input_fails(self, component, invalid_input):
        """Test that invalid input produces appropriate errors."""
        result = component.process(invalid_input)

        assert result is not None
        assert result.valid == False
        assert len(result.errors) > 0
        # Check specific error
        assert any(e.category == "expected_category" for e in result.errors)

    def test_edge_case_handling(self, component):
        """Test edge case handling."""
        # Test with None, empty, etc.
        pass

    # Add more tests...
```

### Common Test Scenarios

**For validators:**
- Valid component passes
- Missing required fields fail
- Invalid field values fail with specific errors
- Security issues detected (XML injection, command injection)
- Edge cases (empty strings, None, very long values)
- Scoring calculation correctness

**For scorers:**
- Perfect input scores 100
- Flawed input scores < 100
- Empty input scores 0
- Multiple components aggregate correctly
- Recommendations generated appropriately
- Breakdown by category/type correct

**For orchestration:**
- Discovery finds valid components
- Execution handles errors gracefully
- Progress reporting works
- Parallel execution correct
- Results aggregate correctly

---

## Integration Guidelines

### Adding New Validator to TestRunner

```python
# 1. Import validator
from src.validators.new_validator import NewValidator

# 2. Initialize in __init__
def __init__(self):
    # ... existing validators ...
    self.new_validator = NewValidator()

# 3. Add to run() method
def run(self, plugin_info):
    # ... existing validation ...

    # Validate new component type
    new_dir = plugin_path / "new-components"
    if new_dir.exists():
        for new_file in new_dir.glob("**/*.ext"):
            component = self._parse_new_file(new_file)
            result = self.new_validator.validate(component, {})
            validation_results.append(result)

# 4. Add parser helper
def _parse_new_file(self, file_path: Path) -> Dict:
    # Parse file and return component dict
    pass
```

### Adding New Scorer to Pipeline

```python
# 1. Import scorer
from src.scoring.new_scorer import NewScorer

# 2. Initialize
def __init__(self):
    # ... existing scorers ...
    self.new_scorer = NewScorer()

# 3. Calculate score
def run(self, plugin_info):
    # ... existing scoring ...

    new_score = self.new_scorer.score(validation_results)

    return {
        # ... existing scores ...
        "new_score": new_score
    }
```

---

## Common Pitfalls

### 1. Skipping RED Phase

❌ **Wrong:** Write implementation first, then tests
✅ **Correct:** Write tests first, watch them fail, then implement

### 2. Tests That Don't Test

❌ **Wrong:**
```python
def test_validator():
    result = validator.validate(data)
    # No assertions!
```

✅ **Correct:**
```python
def test_validator():
    result = validator.validate(data)
    assert result.valid == True
    assert len(result.errors) == 0
```

### 3. Incomplete Error Handling

❌ **Wrong:** Crash on invalid input
✅ **Correct:** Return ValidationResult with appropriate errors

### 4. Not Testing Edge Cases

❌ **Wrong:** Only test happy path
✅ **Correct:** Test None, empty, very long, special characters

### 5. Tight Coupling

❌ **Wrong:** Validators directly depend on each other
✅ **Correct:** Validators are independent, orchestrated by TestRunner

### 6. Hardcoded Values

❌ **Wrong:**
```python
if len(description) < 50:  # Magic number
```

✅ **Correct:**
```python
MIN_DESCRIPTION_LENGTH = 50  # Named constant
if len(description) < MIN_DESCRIPTION_LENGTH:
```

### 7. No Evidence in Commits

❌ **Wrong:** "Added validator" (no test results)
✅ **Correct:** Include test counts and pass/fail evidence in commit message

---

## Development Workflow

### Daily Development Cycle

1. **Pick next task** from priority list
2. **Read task description** in plan carefully
3. **Study reference implementations** for patterns
4. **Follow TDD cycle**:
   - Write tests (RED)
   - Implement (GREEN)
   - Refactor (optional)
   - Verify full suite
   - Commit with evidence
5. **Update plan** with commit hash
6. **Update state.json** with progress

### Parallel Development

If working on multiple tasks:
- Use git worktrees for independent tasks
- Validators can be developed in parallel (2.3-2.7)
- Scorers can be developed in parallel (3.2-3.3)
- Merge to main when tests pass

### Quality Gates

Before merging any task:
- [ ] All new tests pass
- [ ] All existing tests still pass (no regressions)
- [ ] Test coverage >= 80% for new code
- [ ] Code follows existing patterns
- [ ] Commit message includes evidence
- [ ] Plan updated with commit hash

---

## Estimated Timeline

**Conservative estimates (working alone):**

- **Priority 1** (Validators 2.3-2.7): 12-15 hours
- **Priority 2** (Scorers 3.2-3.4): 8-10 hours
- **Priority 3** (User Testing 2.8-2.13): 20-25 hours
- **Priority 4** (Integration & Validation): 8-12 hours

**Total: 48-62 hours** (6-8 working days at 8 hours/day)

**Aggressive estimates (with patterns established):**
- Priority 1: 8-10 hours
- Priority 2: 5-7 hours
- Priority 3: 15-20 hours
- Priority 4: 6-8 hours

**Total: 34-45 hours** (4-6 working days)

---

## Success Criteria

Framework is complete when:

- [ ] All 24 tasks marked [x] in plan
- [ ] All tests passing (target: 100+ tests)
- [ ] Test coverage >= 80%
- [ ] Successfully scored 3+ real plugins
- [ ] Dashboard displays results correctly
- [ ] Documentation complete
- [ ] No P1 issues in self-review

---

## Next Steps

### Immediate (Do Now)

1. **Pick first task:** Task 2.3 (Agent Validator)
2. **Read validation rules** for agents
3. **Start TDD cycle:** Write tests first

### Short-term (This Week)

1. Complete all 5 validators (Priority 1)
2. Update TestRunner to use all validators
3. Test against real plugins

### Medium-term (Next Week)

1. Complete all scorers (Priority 2)
2. Build user testing framework (Priority 3)
3. Generate quality dashboard (Priority 4)

### Long-term (Future)

1. Validate against 10+ real plugins
2. Refine scoring based on feedback
3. Document best practices
4. Consider: GitHub Action integration, CI/CD plugin

---

## Resources

- **Reference code:** `src/validators/skill_validator.py`, `src/scoring/structural_scorer.py`, `src/runner.py`
- **Validation rules:** `.mycelium/context/validation-rules.md`
- **Scoring formulas:** `.mycelium/context/quality-framework.md`
- **Test examples:** `tests/unit/test_skill_validator.py`, `test_structural_scorer.py`, `test_runner.py`
- **Architecture:** `docs/architecture.md`
- **Plan:** `.mycelium/plans/2026-02-13-plugin-testing.md`

---

## Support

If stuck:
1. Review reference implementations
2. Check existing tests for patterns
3. Consult validation-rules.md and quality-framework.md
4. Run pytest with -v flag to see detailed output

Remember: **Tests first, always.** The TDD cycle is non-negotiable.

---

**End of Implementation Guide**

# Comprehensive Catalog of Existing Testing Tools for Claude Code Plugins

**Research Date:** 2026-02-13
**Task:** Survey existing testing tools, validators, and quality frameworks

---

## Executive Summary

This catalog documents **8+ major testing tools** for Claude Code plugins, analyzes gaps in current tooling, and provides actionable recommendations for reuse vs. building new tools.

**Key Findings:**
- Strong triggering validation exists (cc-plugin-eval)
- Good structural validation available (cclint, plugin-dev scripts)
- Major gaps in functional testing, quality scoring, and security scanning
- Recommendation: Reuse 5 existing tools, build 5 new tools

---

## 1. PLUGIN-DEV VALIDATION UTILITIES

### 1.1 validate-hook-schema.sh
**Location:** `plugins/plugin-dev/skills/hook-development/scripts/`

**What it does:** Validates hooks.json structure and syntax

**Usage:** `scripts/validate-hook-schema.sh hooks/hooks.json`

**Capabilities:**
- JSON schema compliance validation
- Hook configuration structure checking
- Required field verification

**Limitations:**
- Known bug: Doesn't support plugin wrapper format properly
- Structure-only validation (no runtime behavior testing)
- Manual execution required

**Status:** **REUSE** - Baseline validation tool

---

### 1.2 validate-agent.sh
**Location:** `plugins/plugin-dev/skills/agent-development/scripts/`

**What it does:** Validates agent definition files

**Capabilities:**
- Required fields: name, description, model, color
- Name formatting rules (alphanumeric start/end, hyphens only)
- Character limits (3-50 characters)

**Limitations:**
- Field-level validation only
- No semantic validation
- Manual execution

**Status:** **REUSE** - Official agent validator

---

### 1.3 test-hook.sh
**Location:** `plugins/plugin-dev/skills/hook-development/scripts/`

**What it does:** Tests hooks with sample input

**Usage:** `./skills/hook-development/scripts/test-hook.sh hooks/my-hook.sh input.json`

**Capabilities:**
- Simulates hook execution
- Validates behavior before deployment
- Immediate feedback

**Limitations:**
- Manual test case creation
- Single-hook testing only
- No automated suite support

**Status:** **REUSE** - Useful for hook development

---

### 1.4 hook-linter.sh
**Location:** `plugins/plugin-dev/skills/hook-development/scripts/`

**What it does:** Checks hook scripts for issues

**Usage:** `./skills/hook-development/scripts/hook-linter.sh hooks/my-hook.sh`

**Capabilities:**
- Common scripting issue identification
- Best practices enforcement
- Actionable feedback

**Limitations:**
- Static analysis only
- May miss runtime errors
- Language-specific

**Status:** **REUSE** - Good for shell script hooks

---

## 2. COMMUNITY TESTING TOOLS

### 2.1 cc-plugin-eval ⭐
**Repository:** [sjnims/cc-plugin-eval](https://github.com/sjnims/cc-plugin-eval)

**What it does:** 4-stage evaluation framework for testing plugin component triggering

**Capabilities:**
- Tests skills, agents, commands, hooks, MCP servers
- Programmatic detection or LLM-only judgment
- Multi-sample judgment for reliability
- Conflict detection
- Session reuse (80% overhead reduction)
- Programmatic API for CI/CD integration
- Configuration via config.yaml

**Usage:**
```bash
npx cc-plugin-eval run -p ./path/to/your/plugin
```

**Strengths:**
- ✅ Comprehensive component coverage
- ✅ Automated triggering validation
- ✅ CI/CD integrable
- ✅ 80% reduction in manual testing

**Limitations:**
- Requires test scenario configuration
- LLM judgment can be non-deterministic
- Focused on triggering, not functionality

**Status:** **REUSE** ⭐ - Best triggering validator available

---

### 2.2 cclint ⭐
**Repository:** [carlrannaberg/cclint](https://github.com/carlrannaberg/cclint)

**What it does:** Comprehensive linter for Claude Code projects

**Capabilities:**
- Agent definition validation
- Command configuration validation
- .claude/settings.json validation
- CLAUDE.md best practices checking
- Custom schema support (Zod)
- Multiple output formats (console, JSON, Markdown)
- CI/CD friendly (configurable exit codes, quiet mode)

**Installation:**
```bash
npm install -g @carlrannaberg/cclint
# or
npx @carlrannaberg/cclint
```

**Usage:**
```bash
cclint                          # Lint current project
cclint --root /path/to/project  # Specific directory
cclint --quiet                  # Quiet mode
```

**Strengths:**
- ✅ Comprehensive validation
- ✅ Multiple output formats
- ✅ Extensible with custom schemas
- ✅ CI/CD ready
- ✅ Fast focused validation

**Limitations:**
- Structure-focused, not runtime behavior
- Requires Node.js

**Status:** **REUSE** ⭐ - Best structural validator

---

### 2.3 klaudiush
**Repository:** [smykla-skalski/klaudiush](https://github.com/smykla-skalski/klaudiush)

**What it does:** Go-based validation dispatcher for Claude Code hooks

**Capabilities:**
- PreToolUse hook interception
- Advanced Bash parsing (mvdan.cc/sh)
- File operation detection
- Project-specific rule enforcement
- Configurable validators
- Multiple configuration sources
- Warning mode (non-blocking)

**Extensibility:**
- Create validators in `internal/validators/{category}/`
- Implement `Validate()` method
- Register in `cmd/klaudiush/main.go`

**Strengths:**
- ✅ Real-time validation during execution
- ✅ Prevents quality issues proactively
- ✅ Highly extensible
- ✅ Language-agnostic

**Limitations:**
- Requires Go runtime
- Hook-specific only
- Requires configuration setup

**Status:** **REUSE** - Best quality gate enforcer

---

### 2.4 CCPI
**Repository:** [jeremylongshore/claude-code-plugins-plus-skills](https://github.com/jeremylongshore/claude-code-plugins-plus-skills)

**What it does:** Package manager with validation for plugins

**Capabilities:**
- Structural validation
- Directory structure verification
- Component integrity checks
- Pre-distribution validation

**Usage:**
```bash
ccpi validate ./my-plugin
```

**Strengths:**
- ✅ Fast structural validation
- ✅ Simple CLI
- ✅ Part of larger ecosystem (270+ plugins, 739 skills)

**Limitations:**
- Structural validation only
- No functional testing
- No triggering validation

**Status:** **REUSE** - Quick structural checks

---

### 2.5 Skill Specification Linter
**Source:** [MCP Market](https://mcpmarket.com/ja/tools/skills/skill-specification-linter)

**What it does:** Validates skills against agentskills.io specification

**Capabilities:**
- agentskills.io standard compliance
- Metadata validation
- Token usage optimization
- Quality assurance

**Strengths:**
- ✅ Enforces industry standard
- ✅ Ensures portability
- ✅ Optimizes efficiency

**Limitations:**
- Specification-focused only
- No functional testing

**Status:** **REUSE** - Ensure portability

---

## 3. CI/CD FOR PLUGINS

### 3.1 Claude Code GitHub Actions ⭐
**Repository:** [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action)

**What it does:** Official GitHub Action for CI/CD integration

**Capabilities:**
- AI-powered code review on PRs
- Automated test scaffolding
- Small refactors
- @claude mention activation
- Issue assignment triggers
- Multiple auth methods (Anthropic API, Bedrock, Vertex AI)

**Setup:**
```bash
/install-github-app  # From Claude Code
```

**Common Patterns:**
- Code review enforcement
- Test generation
- Changelog updates
- Linting checks
- Pre-commit validation

**Strengths:**
- ✅ Official Anthropic support
- ✅ Multiple auth options
- ✅ Flexible triggering
- ✅ Integrates with GitHub workflows

**Limitations:**
- Requires GitHub environment
- API costs for execution

**Status:** **REUSE** ⭐ - Official CI/CD solution

---

## 4. LINTING AND VALIDATION PATTERNS

### 4.1 YAML/JSON Validators
- **yaml-schema-validator** (npm)
- **json-yaml-validate** (GitHub Action)
- **CUE language** for configuration validation

**Use Cases:**
- hooks.json validation
- Agent/command definitions
- settings.json compliance
- Pre-commit validation

---

### 4.2 Markdown Linters

**claude-md-skill**
- Repository: [RedondoK/claude-md-skill](https://github.com/RedondoK/claude-md-skill)
- Transforms AI markdown to pass markdownlint
- Zero violations on first attempt
- GFM compliance

**markdown-linter-fixer-skill**
- Repository: [s2005/markdown-linter-fixer-skill](https://github.com/s2005/markdown-linter-fixer-skill)
- Automatic formatting fixes
- markdownlint-cli2 integration
- SKILL.md quality checks

---

### 4.3 Shell Script Validators

**ShellCheck Integration:**
- Validates shell scripts in hooks
- Common issue identification
- Best practices enforcement
- 10-second timeout
- Used by hook-linter.sh, klaudiush

---

## 5. ADDITIONAL TESTING FRAMEWORKS

### 5.1 Playwright Skill for Testing
**Repository:** [lackeyjb/playwright-skill](https://github.com/lackeyjb/playwright-skill)

**Capabilities:**
- E2E testing automation
- Custom test script generation
- Browser-based validation
- Visual regression testing

**Status:** Useful for web-based plugin testing

---

### 5.2 Sandboxed Evaluation Framework
**Reference:** [Scott Spence - Measuring Claude Code Skill Activation](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals)

**Approach:**
- Isolated Daytona sandboxes
- `claude -p` command testing
- Skill activation reliability measurement
- Baseline performance measurement

**Results:**
- Baseline: 55% activation (no intervention)
- With forced-eval hook: 100% activation
- Zero hallucinated activations

**Status:** Research pattern to productionize

---

### 5.3 Forced-Eval Hook Pattern
**Reference:** [Scott Spence - Reliable Skill Activation](https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably)

**Mechanism:**
- UserPromptSubmit hook
- Explicit skill evaluation
- YES/NO decision forcing
- 100% activation accuracy

**Implementation:**
```
UserPromptSubmit → Evaluate Each Skill → YES/NO → Proceed
```

**Status:** Pattern to implement in framework

---

## ANALYSIS OF GAPS

### 🔴 Critical Gaps

1. **Integrated Testing Suite**
   - No comprehensive framework combining all validation types
   - Fragmented tools across repos
   - Need unified testing CLI

2. **Functional Testing Framework**
   - Most tools focus on structure/schema
   - Limited actual behavior testing
   - No MCP mocking patterns
   - Missing plugin-specific assertion libraries

3. **Quality Scoring System**
   - No aggregated quality metrics
   - No industry-standard plugin quality score
   - Missing component-level scoring

4. **Security Testing**
   - No dedicated security scanner
   - Missing injection vulnerability testing
   - No secrets detection
   - Limited allowed-tools validation

5. **Regression Testing**
   - No snapshot testing for outputs
   - No version comparison tools
   - Missing change impact analysis

### 🟡 Medium Priority Gaps

6. **Performance Testing**
   - No token efficiency measurement
   - Missing response time benchmarking
   - No load testing for hooks

7. **Coverage Metrics**
   - No trigger scenario coverage
   - Missing edge case identification
   - No test completeness measurement

8. **Documentation Quality**
   - No automated completeness checking
   - Missing example validation
   - No reference link verification

9. **Cross-Platform Testing**
   - Limited testing across Claude.ai/Code/API
   - No compatibility validation

10. **User Experience Testing**
    - No conversation flow validation
    - Missing prompt clarity assessment

---

## RECOMMENDATIONS: REUSE VS. BUILD

### ✅ REUSE (High Priority)

1. **cc-plugin-eval** ⭐
   - **Use for:** Triggering tests, activation validation
   - **Extend:** Add custom scenarios, integrate into CI/CD
   - **Priority:** Critical - best triggering validator

2. **cclint** ⭐
   - **Use for:** Pre-commit checks, structure validation
   - **Extend:** Add custom schemas for project rules
   - **Priority:** Critical - best structural validator

3. **Claude Code GitHub Actions** ⭐
   - **Use for:** CI/CD integration, PR reviews
   - **Extend:** Custom workflows for plugin testing
   - **Priority:** High - official support

4. **klaudiush**
   - **Use for:** Quality gates, git workflow enforcement
   - **Extend:** Add plugin-specific validators
   - **Priority:** High - real-time validation

5. **plugin-dev scripts**
   - **Use for:** Basic validation during development
   - **Extend:** Integrate into larger pipelines
   - **Priority:** Medium - official baseline

---

### 🔨 BUILD NEW (High Priority)

1. **Unified Testing CLI** 🎯
   - **Why:** No single orchestration tool exists
   - **What:** CLI running structural, functional, triggering, quality tests
   - **Integration:** Leverage cc-plugin-eval, cclint, plugin-dev
   - **Output:** Unified test report across all dimensions
   - **Priority:** CRITICAL

2. **Functional Testing Framework** 🎯
   - **Why:** Gap in actual behavior testing
   - **What:** Assertion library + test runner for functionality
   - **Features:** MCP mocking, conversation simulation, output validation
   - **Pattern:** Jest/Vitest-like but plugin-aware
   - **Priority:** CRITICAL

3. **Quality Scorecard Generator** 🎯
   - **Why:** No aggregated quality metrics
   - **What:** Tool producing comprehensive quality scores
   - **Metrics:** Structure, triggering, documentation, security
   - **Output:** README badge, detailed report
   - **Priority:** CRITICAL

4. **Security Scanner** 🎯
   - **Why:** Security testing minimal
   - **What:** Vulnerability scanner for plugins
   - **Checks:** allowed-tools, secrets, injection risks
   - **Integration:** Pre-commit + CI/CD
   - **Priority:** HIGH

5. **Regression Testing Suite** 🎯
   - **Why:** No standardized regression testing
   - **What:** Snapshot testing for outputs, conversation flows
   - **Features:** Version comparison, change impact
   - **Integration:** Part of unified CLI
   - **Priority:** HIGH

---

### 🔨 BUILD NEW (Medium Priority)

6. **Coverage Analyzer**
   - Trigger scenario coverage measurement
   - Edge case identification
   - Test completeness suggestions

7. **Performance Profiler**
   - Token usage tracking
   - Response time benchmarking
   - Resource consumption monitoring

8. **Documentation Validator**
   - Completeness checking
   - Example code validation
   - Reference link verification

---

## COMPARISON TABLE

| Tool | Type | Capabilities | Gaps | Status |
|------|------|--------------|------|--------|
| **cc-plugin-eval** | Triggering | Skills, agents, commands, hooks, MCP validation; 80% overhead reduction | No functional testing; no output validation | ⭐ REUSE |
| **cclint** | Linting | Project structure, agents, commands, settings; custom schemas; CI/CD ready | No runtime testing; no triggering | ⭐ REUSE |
| **klaudiush** | Hook Validator | Real-time PreToolUse validation; extensible; git workflows | Hook-specific; requires Go | REUSE |
| **CCPI** | Package Manager | Structural validation; directory checks | Basic validation only | REUSE |
| **plugin-dev scripts** | Official Tools | validate-hook-schema, validate-agent, test-hook | Manual execution; limited scope | REUSE |
| **GitHub Actions** | CI/CD | Code review; test generation; automation | Requires GitHub; API costs | ⭐ REUSE |

---

## IMPLEMENTATION ROADMAP

### Immediate Actions (Week 1)
1. ✅ Adopt **cc-plugin-eval** for triggering validation
2. ✅ Integrate **cclint** for pre-commit checks
3. ✅ Use **plugin-dev scripts** during development
4. ✅ Implement **forced-eval hook pattern** for critical skills

### Short-term (1-3 months)
1. 🔨 Build **Unified Testing CLI** orchestrating existing tools
2. 🔨 Create **Functional Testing Framework** for behavior validation
3. 🔨 Develop **Quality Scorecard Generator** for metrics
4. 🔨 Implement **Security Scanner** for vulnerabilities

### Medium-term (3-6 months)
1. 🔨 Build **Regression Testing Suite** with snapshots
2. 🔨 Create **Coverage Analyzer** for completeness
3. 🔨 Develop **Performance Profiler** for optimization
4. 🔨 Build **Documentation Validator** for quality

---

## TOOL INTEGRATION STRATEGY

```
Development Workflow:
├── Pre-commit: cclint + Security Scanner
├── Development: plugin-dev scripts + Functional Testing Framework
├── CI/CD: cc-plugin-eval + Unified Testing CLI + GitHub Actions
└── Release: Quality Scorecard Generator + Regression Suite
```

---

## SOURCES

- [Create plugins - Claude Code Docs](https://code.claude.com/docs/en/plugins)
- [plugin-dev - GitHub](https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev)
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks)
- [validate-agent.sh](https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/agent-development/scripts/validate-agent.sh)
- [cc-plugin-eval](https://github.com/sjnims/cc-plugin-eval)
- [CCPI](https://github.com/jeremylongshore/claude-code-plugins-plus-skills)
- [cclint](https://github.com/carlrannaberg/cclint)
- [klaudiush](https://github.com/smykla-skalski/klaudiush)
- [Claude Code GitHub Actions](https://github.com/anthropics/claude-code-action)
- [claude-md-skill](https://github.com/RedondoK/claude-md-skill)
- [markdown-linter-fixer-skill](https://github.com/s2005/markdown-linter-fixer-skill)
- [playwright-skill](https://github.com/lackeyjb/playwright-skill)
- [Scott Spence - Skill Activation Measurement](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals)
- [Scott Spence - Reliable Skill Activation](https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably)

---

**Research completed:** 2026-02-13
**Tools cataloged:** 8+ major tools
**Gaps identified:** 10 critical/medium gaps
**Recommendations:** 5 tools to reuse, 5 tools to build

---
name: dependency-audit
description: |
  Use this skill when the user wants to audit dependencies for security
  vulnerabilities, outdated versions, or license issues. Triggers on:
  "audit dependencies / packages", "check for vulnerabilities", "are my deps
  up to date", "what needs upgrading", "license audit", "security scan results".

  Also use when CI flags dependency issues and the user pastes the output
  asking for help.

  Do NOT use for: writing code that uses a specific library, or upgrading a
  single specific package (just bump the version).
---

# Dependency Audit

You translate noisy audit-tool output into actionable triage. You distinguish
real risks from theatre, fixable from unfixable, and explain what to do in
what order.

## Process when activated

### Step 1: Identify the package manager

Detect by looking for files in the project root:
- `package.json` + `package-lock.json` → npm
- `package.json` + `pnpm-lock.yaml` → pnpm
- `package.json` + `yarn.lock` → Yarn
- `pyproject.toml` + `poetry.lock` → Poetry
- `pyproject.toml` + `uv.lock` → uv
- `requirements.txt` → pip
- `pom.xml` → Maven
- `build.gradle` / `build.gradle.kts` → Gradle
- `Cargo.toml` → Cargo
- `go.mod` → Go modules
- `Gemfile.lock` → Bundler

If multiple lockfiles exist (monorepo), ask which to focus on.

### Step 2: Run the right audit command

| Tool | Audit command |
|------|---------------|
| npm | `npm audit --json` |
| pnpm | `pnpm audit --json` |
| Yarn (Berry) | `yarn npm audit --json` |
| Poetry | `poetry check` + `pip-audit` |
| uv | `uv pip check` + `pip-audit` |
| pip | `pip-audit` |
| Maven | `mvn dependency-check:check` (OWASP) |
| Gradle | `./gradlew dependencyCheckAnalyze` |
| Cargo | `cargo audit` |
| Go | `govulncheck ./...` |
| Bundler | `bundle audit` |

DON'T just run it and dump the output. Parse it. Categorize. Triage.

### Step 3: Categorize findings

For each vulnerability, classify:

#### Severity (use the tool's CVSS-mapped severity)
- **Critical** (CVSS 9.0-10.0)
- **High** (CVSS 7.0-8.9)
- **Medium** (CVSS 4.0-6.9)
- **Low** (CVSS 0.1-3.9)

#### Exploitability in THIS project

Critical questions to ask about each finding:
1. **Is this dependency actually used at runtime?**
   - Dev-only deps (testing, build tools) have lower real-world risk
2. **Does the vulnerable code path get exercised?**
   - A `prototype pollution` vuln in a JSON parser only matters if you parse
     untrusted JSON
3. **Is the dependency direct or transitive?**
   - Transitive vulns may not be fixable without upstream patches
   - Direct deps are easy to upgrade

#### Fixability
- **Direct fix available** — bump the package
- **Indirect fix** — upstream package needs to bump first
- **No fix yet** — vulnerability disclosed but no patched version
- **Breaking change required** — fix is in a major version with API breaks

### Step 4: Triage

Output in this order:

#### 🔴 Fix immediately (Critical / High + exploitable + fixable)
For each:
- Package name and current version
- Vulnerable to: [CVE or summary]
- Risk in this project: [specific to your code]
- Fix: `pnpm up <package>@<version>` (or equivalent command)
- Estimated effort: [trivial / small / medium / large]

#### 🟡 Plan to fix (Medium severity OR breaking-change fix)
Same format, lower priority.

#### 🟢 Track (Low severity, unfixable, or low-exploitability)
Brief list:
- Package, severity, why deferred
- "Recheck monthly" or "wait for upstream fix"

#### 🚫 Ignore (false positives, dev-only, sandboxed)
Briefly note why.

#### 📦 Outdated but not vulnerable

If the user also wants freshness info, list the top 5-10 packages most
out-of-date. For each:
- Current → Latest
- Days behind
- Likely upgrade complexity (patch / minor / major)
- Highlight any majors that are >12 months behind (real upgrade pain ahead)

#### 📜 License findings

If the project has license-sensitive code (commercial product, regulated
industry):

Flag any:
- GPL/AGPL transitively pulled in (copyleft)
- Unlicensed packages
- License changes since last audit

For each flagged license, note:
- The package
- Its license
- Whether it's allowed by [the project's policy if known]
- Action: review/replace/accept

### Step 5: Generate the upgrade commands

Provide a single block the user can review and run:

```bash
# Critical/High fixes (direct upgrades)
pnpm up package-a@1.2.3 package-b@4.5.6

# Then re-run the audit to verify
pnpm audit
```

If multiple commands across categories, group them clearly.

If a fix requires a major version bump, NOTE separately:
> "package-c needs a major bump (1.x → 2.x). Likely API breaks. Suggest:
> 1. Read changelog: [URL]
> 2. Run upgrade in a feature branch
> 3. Run tests, fix breaks, then merge"

### Step 6: What you don't do

- **Don't run upgrade commands without confirmation.** Show the plan, get
  approval, then run if asked.
- **Don't pretend a vulnerability is exploitable when it isn't.** Be honest
  about which findings are theatre.
- **Don't recommend tools that aren't in the project's package manager
  ecosystem.** Don't suggest snyk/dependabot if they're using bare
  `npm audit`.
- **Don't ignore the lockfile.** Always pin to specific versions, not
  ranges, when fixing security issues.

## Special cases

### Monorepos

For monorepos with multiple `package.json`s:
- Run audit at the workspace root (e.g., `pnpm audit -r`)
- Group findings by workspace
- Same package vulnerable in 5 workspaces is one fix at the root if hoisted

### Yarn 1 vs Yarn Berry

These have different audit commands:
- Yarn 1: `yarn audit`
- Yarn Berry: `yarn npm audit`

Detect by Yarn version: `yarn --version`.

### Old projects with hundreds of vulnerabilities

If the audit returns 100+ findings, don't try to triage all of them:

> "This project has 247 audit findings. That's too many to triage individually.
> Focused approach:
> 1. Filter to Critical/High only ([N] findings)
> 2. Filter to direct dependencies only ([M] findings)
> 3. Tackle those first
> 
> The rest are likely transitive low-severity issues. Address them via
> regular dependency hygiene (Dependabot, Renovate, monthly upgrade days)
> rather than a one-time audit."

### Vulnerabilities in transitive dependencies

Common pattern: package X depends on Y depends on Z, and Z is vulnerable.

Options:
1. Wait for Y to bump Z (often the right call)
2. Use a resolution to override Z directly (npm `overrides`, pnpm `overrides`,
   Yarn `resolutions`)
3. Replace X with an alternative

Show all three, note the trade-off:
> "Override Z directly = quick fix but you're now responsible for tracking Z's
> updates. Wait for Y = no work but vulnerability persists."

### Zero-day in a critical dep

If a CVE just dropped on something like `lodash` or `react`:

1. Confirm the CVE is real (not a typosquat from a junk advisory)
2. Check the patched version is published and not just announced
3. Pin to the patched version, not a range
4. After upgrade, re-run audit AND tests

## Anti-patterns to avoid

- Treating every CVE as urgent (most aren't)
- Treating vulnerabilities in dev deps as urgent (they usually aren't)
- Auto-running `npm audit fix --force` (can break things)
- Ignoring the actual CVE description ("CVSS 9.8" without reading why)
- Bumping major versions to fix a low-severity issue (cure > disease)
- Adding new tools when the language's built-in audit is sufficient

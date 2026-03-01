# 🤖 Self-Healing CI Pipeline Documentation

## Overview

The **Self-Healing CI Pipeline** is an advanced GitHub Actions workflow that automatically detects, analyzes, and fixes failing tests and builds. It reduces Mean Time To Recovery (MTTR) through AI-powered incident analysis and automated remediation suggestions.

> **Status**: Production-Ready | **Latest Version**: 1.0.0

---

## 🎯 Core Features

### 1. **🔄 Flaky Test Auto-Healing**

**What it does:**
- Automatically detects tests that fail intermittently
- Reruns failed tests to identify flaky behavior
- Tracks flaky test patterns over time

**How it works:**
```
Test Fails → Auto-Retry → Analysis → Classification:
✅ Consistent Pass → Not flaky
❌ Consistent Fail → Real bug (needs fix)
⚠️ Mixed Results → Flaky Test (needs investigation)
```

**Benefits:**
- Reduces false negatives from transient failures
- Saves developer time on debugging environment issues
- Provides data for test reliability improvement

### 2. **📊 MTTR Dashboard**

**What it tracks:**
- **Build Success Rate**: Percentage of builds that pass (Last 30 runs)
- **Mean Time To Recovery (MTTR)**: Average time to fix broken builds
- **Auto-Fixed Incidents %**: Percentage of failures caught and resolved automatically
- **Flaky Test Count**: Number of intermittent test failures detected

**Dashboard Features:**
- Real-time HTML dashboard at `.github/metrics/dashboard.html`
- Machine-readable metrics JSON at `.github/metrics/ci-metrics.json`
- Historical data tracking (30-day rolling window)
- Automatic git commits for metrics history

**Metrics Storage Structure:**
```json
{
  "timestamp": "2026-03-01T10:30:00",
  "workflow_run_id": "123456",
  "branch": "refs/heads/main",
  "test_passed": true,
  "test_duration_seconds": 145,
  "build_failure_rate": 5.2,
  "mttr_minutes": 2.3,
  "auto_fixed_incidents_percent": 60.0,
  "flaky_tests_count": 2
}
```

### 3. **🤖 AI Incident Summary**

**What it provides:**
- Root cause analysis for test failures
- Confidence scoring for suggestions
- Automated PR comments with analysis

**Example Output:**
```
❌ Build Failed
Root Cause: Timeout in database connection
Suggested Fix: Increase test timeout or add connection pooling
Confidence: 87%
```

**Detection Patterns:**
- **Timeout Issues**: Detection of deadline exceeded errors
- **Network Connectivity**: Connection refused, DNS resolution failures
- **Import Errors**: Missing dependencies or file paths
- **Assertion Failures**: Test logic issues
- **Runtime Panics**: Fatal runtime errors

---

## 🚀 Getting Started

### Prerequisites
- GitHub repository with GitHub Actions enabled
- Go 1.25.0+ (for this project)
- Permission to modify `.github/workflows/`

### Installation Steps

1. **Copy the workflow file** to your repository:
   ```bash
   cp .github/workflows/self-healing-ci.yml <your-repo>/.github/workflows/
   ```

2. **Verify workflow permissions** in your repository settings:
   - Go to **Settings > Actions > General**
   - Ensure "Read and write permissions" is enabled for workflows
   - Allow "Allow GitHub Actions to create and approve pull requests"

3. **Create metrics directory** (optional, auto-created):
   ```bash
   mkdir -p .github/metrics
   ```

4. **Commit and push**:
   ```bash
   git add .github/workflows/self-healing-ci.yml
   git commit -m "🤖 Add self-healing CI pipeline"
   git push
   ```

5. **Trigger workflow**:
   - Create a pull request or push to main branch
   - Navigate to **Actions** tab to monitor execution

---

## 📋 Workflow Jobs

### Job 1: `test-with-flaky-detection` (45-60 min)
**Purpose**: Execute tests and detect flaky patterns

**Outputs**:
- `test_failed`: Boolean indicating test failure
- `failed_tests`: List of failed test names
- `failure_summary`: Human-readable failure summary
- `flaky_tests`: Tests with intermittent failures
- `test_duration`: Total test execution time

**Artifacts**:
- `test-result.json`: Raw test output (JSON)
- `coverage.html`: Coverage report
- `coverage.out`: Coverage data

---

### Job 2: `analyze-failures` (5-10 min)
**Purpose**: AI-powered root cause analysis

**Triggers**: Only on test failures

**Actions**:
- Parses test output for error patterns
- Assigns root causes with confidence scores
- Posts detailed analysis to PR comments

**Outputs**:
- Analysis report saved to `/tmp/analysis_report.json`
- PR comment with findings and suggestions

---

### Job 3: `collect-metrics` (2-5 min)
**Purpose**: Track MTTR and reliability metrics

**Metrics Collected**:
- Build success/failure status
- Test duration in seconds
- Flaky test occurrences
- Failure rate (7-day average)
- MTTR in minutes
- Auto-fix percentage

**Outputs**:
- Updated `.github/metrics/ci-metrics.json`
- Regenerated dashboard HTML
- Git commit with metrics (on push events)

---

### Job 4: `suggest-fixes` (2-3 min)
**Purpose**: Automated remediation suggestions

**Triggers**: Only on PR test failures

**Actions**:
- Generates context-aware fix suggestions
- Posts interactive PR comment
- Updates comment on subsequent runs

**Suggestions Include**:
- Common patterns (flaky tests, timeouts, etc.)
- Actionable remediation steps
- Affected test names

---

## 🔧 Configuration

### Environment Variables

```yaml
GO_VERSION: '1.25.0'        # Go version to use
CACHE_VERSION: 'v1'         # Cache invalidation key
```

### Customization Options

#### 1. Adjust Test Timeout
In `test-with-flaky-detection` job:
```yaml
- name: 🧪 Run unit tests
  run: go test ... -timeout=5m ...  # Change 5m to desired duration
```

#### 2. Change Retry Count
In auto-retry section:
```yaml
MAX_RETRIES=3  # Change to number of retries desired
```

#### 3. Modify Pattern Detection
In `analyze-failures` job, edit Python section:
```python
patterns = {
    "custom_pattern": {
        "regex": r"your_regex_here",
        "cause": "What caused it",
        "fix": "How to fix it"
    }
}
```

#### 4. Update Dashboard Refresh Interval
Add schedule trigger:
```yaml
on:
  schedule:
    - cron: '0 * * * *'  # Hourly
```

---

## 📊 Metrics & Dashboard

### Accessing the Dashboard

1. **Local View** (after workflow completes):
   ```bash
   open .github/metrics/dashboard.html
   ```

2. **Raw Metrics** (for integration):
   ```bash
   cat .github/metrics/ci-metrics.json
   ```

3. **Webhook Integration** (optional):
   ```bash
   # Export metrics to external monitoring system
   curl -X POST https://your-metrics-endpoint.com/ci-metrics \
     -d @.github/metrics/ci-metrics.json
   ```

### Interpreting Metrics

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Build Success Rate | >95% | 85-95% | <85% |
| MTTR | <5 min | 5-15 min | >15 min |
| Auto-Fixed % | >50% | 25-50% | <25% |
| Flaky Tests | 0 | 1-3 | >3 |

---

## 🔐 Permissions Required

```yaml
permissions:
  contents: read          # Read repo contents
  checks: write           # Write check runs (for test reports)
  pull-requests: write    # Post comments on PRs
  issues: write           # Create/update issues
  actions: read           # Read workflow history
```

> **Security Note**: Metrics are stored in repository, visible to repo members. For sensitive environments, restrict branch access.

---

## 🐛 Troubleshooting

### Issue: Workflow not triggering

**Solution**:
- Check workflow file syntax: `gh workflow validate`
- Verify push/PR events in workflow `on:` section
- Ensure branch protection rules don't block workflows

### Issue: Tests not retrying on failure

**Solution**:
- Verify `continue-on-error: true` is set in retry step
- Check test output format in `test-result.json`
- Review Python parsing logic in `parse-failures` step

### Issue: Dashboard not updating

**Solution**:
- Verify `.github/metrics/` directory exists
- Check git permissions for metrics commit
- Review workflow output for Python errors

### Issue: PR comments not posting

**Solution**:
- Verify `pull-requests: write` permission
- Check workflow has access to PR context (`github.event_name == 'pull_request'`)
- Review GitHub API rate limits

---

## 📈 Performance Tuning

### Reduce Workflow Duration

1. **Parallel Test Execution** (already enabled):
   ```yaml
   go test ... -parallel=8 ...  # Increase for more parallelism
   ```

2. **Skip Slow Tests Locally**:
   ```yaml
   -timeout=3m  # Reduce from 5m
   ```

3. **Cache Optimization**:
   - Clear cache manually: Actions → Delete all caches
   - Cache bust key: Update `CACHE_VERSION`

### Reduce False Positives

1. **Increase Retry Attempts**:
   ```bash
   MAX_RETRIES=5  # Was 3
   ```

2. **Longer Test Timeout**:
   ```yaml
   -timeout=10m  # Was 5m
   ```

---

## 🔗 Integration Examples

### Integration with Slack

Add to workflow:
```yaml
- name: 📢 Notify Slack
  if: failure()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -H 'Content-Type: application/json' \
      -d '{
        "text": "❌ CI Pipeline Failed",
        "blocks": [{
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "*Build*: ${{ github.run_id }}\n*Status*: Failed\n*Branch*: ${{ github.ref }}"
          }
        }]
      }'
```

### Integration with JIRA

```yaml
- name: 📋 Create JIRA Issue
  if: failure()
  run: |
    curl -X POST https://your-jira.atlassian.net/rest/api/3/issues \
      -H "Authorization: Bearer ${{ secrets.JIRA_TOKEN }}" \
      -d '{
        "fields": {
          "project": {"key": "CI"},
          "summary": "Build failed on main",
          "description": "MTTR: ${{ needs.collect-metrics.outputs.mttr_minutes }}m"
        }
      }'
```

---

## 📚 Advanced Topics

### Custom Analysis Patterns

Extend root cause detection in `analyze-failures` job:

```python
patterns = {
    "database": {
        "regex": r"(?i)(database|sql|connection pool)",
        "cause": "Database connectivity issue",
        "fix": "Check database credentials and connection pool settings"
    },
    "memory": {
        "regex": r"(?i)(out of memory|OOM|heap)",
        "cause": "Insufficient memory",
        "fix": "Increase runner memory or optimize test memory usage"
    }
}
```

### Webhook Notifications

Send metrics to external systems:

```python
import requests

metrics = {...}
requests.post(
    "https://your-metrics-api.com/ci/metrics",
    json=metrics,
    headers={"Authorization": f"Bearer {os.environ['METRICS_TOKEN']}"}
)
```

### Custom Dashboard

Replace generated HTML with your own:

```bash
# .github/scripts/custom-dashboard.py
def generate_dashboard(metrics):
    # Your custom HTML generation
    return html_content
```

---

## 📞 Support & Feedback

- **Issues**: Report at GitHub Issues
- **Discussions**: GitHub Discussions
- **Contributing**: See CONTRIBUTING.md

---

## 📄 License

MIT License - See LICENSE file

---

## 🎓 Learning Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Flaky Test Detection Patterns](https://example.com)
- [MTTR Best Practices](https://example.com)
- [CI/CD Automation Guide](https://example.com)

---

**Last Updated**: March 2026  
**Maintained by**: GitHub Self-Healing CI Team

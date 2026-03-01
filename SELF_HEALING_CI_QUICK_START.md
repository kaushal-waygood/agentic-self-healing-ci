# 🤖 Self-Healing CI - Quick Reference Card

## One-Line Summary
**Enterprise-grade GitHub Actions CI pipeline that auto-detects failing tests, analyzes root causes with AI, and tracks MTTR metrics through an interactive dashboard.**

---

## 🚀 In 30 Seconds

```
The pipeline:
1. ✅ Runs your tests + reruns failures (detects flaky tests)
2. 🔍 Analyzes errors with ML-like pattern matching
3. 💬 Posts findings to PR comments with fix suggestions
4. 📊 Tracks metrics (success rate, MTTR, auto-fixed %)
5. 📈 Generates beautiful dashboard showing trends
```

---

## 📋 File Locations

```
.github/
├── workflows/
│   ├── self-healing-ci.yml          ← Main workflow (YAML)
│   └── SELF_HEALING_CI.md           ← Full documentation
├── metrics/
│   ├── ci-metrics.json              ← Machine-readable metrics
│   └── dashboard.html               ← Interactive dashboard

scripts/
├── incident_analyzer.py             ← AI root cause detector
└── flaky_test_healer.py            ← Flaky test analyzer

schemas/
└── ci-metrics.schema.json           ← Metrics JSON schema

SELF_HEALING_CI_SETUP.md             ← Setup guide (THIS FILE)
```

---

## ⚡ Setup Checklist

- [ ] Workflow file exists at `.github/workflows/self-healing-ci.yml`
- [ ] Enable workflow permissions (Settings → Actions → General)
- [ ] Create `.github/metrics/` directory
- [ ] Commit and push
- [ ] Create PR or push to main to trigger workflow
- [ ] Monitor in Actions tab

---

## 🎯 Core Features

### 1️⃣ Flaky Test Detection
```bash
# Automatically detected Test fails → Auto-Retry → Classification
# Check: Workflow output logs
```

### 2️⃣ AI Root Cause Analysis
```bash
# Automatically detects: Timeouts, Network errors, Import issues, etc.
# Check: Pull request comments (bot will post analysis)
```

### 3️⃣ MTTR Metrics Dashboard
```bash
# View at: .github/metrics/dashboard.html
# Or raw JSON: .github/metrics/ci-metrics.json
# Metrics: Success rate, MTTR, Auto-fix %, Flaky count
```

---

## 📊 Key Metrics Explained

| Metric | What It Means | Good Value |
|--------|---------------|------------|
| **Build Success Rate** | % of passing CI runs | >95% |
| **MTTR (Minutes)** | Avg time to fix failures | <5 min |
| **Auto-Fixed %** | % of issues auto-resolved | >50% |
| **Flaky Tests** | Tests failing intermittently | 0 |

---

## 🔍 Troubleshooting Quick Fixes

### Issue: Workflow not triggering
```bash
# Solution 1: Manually trigger
# Go to Actions → Self-Healing CI Pipeline → Run workflow

# Solution 2: Check workflow syntax
gh workflow validate .github/workflows/self-healing-ci.yml
```

### Issue: Tests not retrying
```bash
# Check if continue-on-error is set in workflow
grep -A2 "retry-tests" .github/workflows/self-healing-ci.yml
```

### Issue: Dashboard not showing
```bash
# Verify metrics file exists
ls -la .github/metrics/

# Check metrics content
cat .github/metrics/ci-metrics.json | jq '.'
```

### Issue: PR comments not appearing
```bash
# Verify workflow has permissions
# Settings → Actions → General
# ✅ Read and write permissions
# ✅ Allow pull request comments
```

---

## 🎛️ Common Customizations

### Increase Test Timeout (for slow tests)
```yaml
# In .github/workflows/self-healing-ci.yml, find:
go test ... -timeout=5m ...
# Change 5m to 10m, 15m, etc.
```

### Change Retry Count (for flaky tests)
```yaml
# Find line: MAX_RETRIES=3
# Change 3 to higher number for more retries
```

### Disable Auto-Retry (to see actual failures)
```bash
# Comment out the "🔄 Auto-Retry Failed Tests" step
```

### Send Metrics to Slack
```yaml
# Add job at end of workflow:
- name: 📢 Notify Slack
  run: curl -X POST ${{ secrets.SLACK_WEBHOOK }} ...
```

---

## 💻 CLI Usage (Advanced)

### Analyze Test Results
```bash
python3 scripts/incident_analyzer.py test-result.json incident-summary.json
```

### Detect Flaky Tests
```bash
python3 scripts/flaky_test_healer.py --analyze test-result.json
```

### Generate Metrics Report
```bash
python3 scripts/flaky_test_healer.py --generate-report
```

---

## 🔗 Integration Hooks

### Post to Slack
```yaml
uses: slackapi/slack-github-action@v1
with:
  webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

### Create JIRA Issues
```bash
curl https://your-jira.atlassian.net/rest/api/3/issues \
  -H "Authorization: Bearer ${{ secrets.JIRA_TOKEN }}" -d '{...}'
```

### Send to DataDog
```bash
curl https://api.datadoghq.com/api/v1/series \
  -H "DD-API-KEY: ${{ secrets.DATADOG_API_KEY }}" \
  -d @.github/metrics/ci-metrics.json
```

---

## ❓ FAQ

**Q: Do I need to change my existing tests?**  
A: No! Workflow works with existing test suites.

**Q: Does this work with my language?**  
A: Yes, with modification. Workflow uses generic JSON parsing.

**Q: How much storage do metrics use?**  
A: ~2KB per run = ~1MB per year (minimal).

**Q: Is my data exposed?**  
A: No. Metrics stored in private repo. Use secrets for sensitive data.

**Q: Can I disable auto-retry?**  
A: Yes, comment out the retry step in workflow.

---

## 📞 Quick Support Links

- **Full Docs**: [SELF_HEALING_CI.md](.github/workflows/SELF_HEALING_CI.md)
- **Setup Guide**: [SELF_HEALING_CI_SETUP.md](./SELF_HEALING_CI_SETUP.md)
- **Issues**: [GitHub Issues](https://github.com/github/gh-aw/issues)

---

## 🎓 Next Steps

1. **Review** the workflow file
2. **Check** metrics permissions
3. **Push** a test commit to trigger
4. **Browse** Actions tab to monitor
5. **View** generated PR comments
6. **Open** dashboard in browser

---

## 🎉 You're All Set!

Your repo now has:
- ✅ Auto-healing CI pipeline
- ✅ Flaky test detection
- ✅ AI root cause analysis
- ✅ MTTR dashboard
- ✅ Automated fix suggestions

**Watch your CI health improve! 📈**

---

**Version**: 1.0.0 | **Last Updated**: March 2026 | **Status**: Production Ready ✅

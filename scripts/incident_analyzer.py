#!/usr/bin/env python3
"""
AI-Powered CI Incident Summary Generator

This script analyzes failed CI builds and generates AI-powered incident summaries
with root cause detection and remediation suggestions.

Usage:
    python3 incident_analyzer.py <test-result-json> <output-json>

Environment Variables:
    OPENAI_API_KEY (optional): For advanced LLM-based analysis
    CONFIDENCE_THRESHOLD: Minimum confidence score (default: 50)
"""

import json
import re
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class SeverityLevel(Enum):
    """Severity classification for incidents"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RootCauseCategory(Enum):
    """Categories of root causes"""
    TIMEOUT = "timeout"
    NETWORK = "network"
    IMPORT_ERROR = "import_error"
    ASSERTION = "assertion"
    PANIC = "panic"
    RESOURCE = "resource"
    CONFIG = "config"
    UNKNOWN = "unknown"


@dataclass
class RootCause:
    """Root cause detection model"""
    category: str
    description: str
    pattern: str
    confidence: int
    examples: List[str]
    suggested_fix: str
    priority: int


@dataclass
class IncidentSummary:
    """Complete incident summary"""
    timestamp: str
    incident_id: str
    title: str
    description: str
    severity: str
    test_failures: List[Dict]
    root_causes: List[RootCause]
    affected_components: List[str]
    suggested_fixes: List[Dict]
    overall_confidence: int
    impact_score: int
    estimated_mttr_minutes: int


class IncidentAnalyzer:
    """Analyzes CI failures and generates incident summaries"""
    
    # Pattern library for root cause detection
    PATTERNS = {
        RootCauseCategory.TIMEOUT: {
            "regex": [
                r"(?i)(timeout|deadline exceeded|context deadline|timed out)",
                r"(?i)(test timeout|execution timeout)",
                r"(?i)\b(TIMEOUT|DEADLINE)\b"
            ],
            "description": "Test timeout or deadline exceeded",
            "fix": "Increase test timeout, optimize slow operations, or check for deadlocks",
            "severity": SeverityLevel.HIGH,
            "priority": 1
        },
        RootCauseCategory.NETWORK: {
            "regex": [
                r"(?i)(connection refused|network unreachable|socket error)",
                r"(?i)(dns resolution failed|getaddrinfo failed)",
                r"(?i)(ECONNREFUSED|ENETUNREACH|EAI_NONAME)"
            ],
            "description": "Network connectivity or DNS issue",
            "fix": "Check network dependencies, mock external services, verify DNS",
            "severity": SeverityLevel.HIGH,
            "priority": 2
        },
        RootCauseCategory.IMPORT_ERROR: {
            "regex": [
                r"(?i)(no such file|import error|cannot find)",
                r"(?i)(undefined|not found|missing import)",
                r"(?i)(cannot open|file not found)"
            ],
            "description": "Missing dependency or file import",
            "fix": "Verify all dependencies are installed, check import paths",
            "severity": SeverityLevel.MEDIUM,
            "priority": 3
        },
        RootCauseCategory.ASSERTION: {
            "regex": [
                r"(?i)(assertion failed|expected not matched)",
                r"(?i)(not equal|should equal|equals failed)",
                r"AssertionError|\.Fail\(\)"
            ],
            "description": "Test assertion failure",
            "fix": "Review test logic, verify expected values, check test data",
            "severity": SeverityLevel.MEDIUM,
            "priority": 4
        },
        RootCauseCategory.PANIC: {
            "regex": [
                r"(?i)(panic|fatal error|segmentation fault)",
                r"(?i)(runtime error|fatal)",
                r"panic:|fatal:"
            ],
            "description": "Runtime panic or fatal error",
            "fix": "Add error handling, add nil checks, validate inputs",
            "severity": SeverityLevel.CRITICAL,
            "priority": 0
        },
        RootCauseCategory.RESOURCE: {
            "regex": [
                r"(?i)(out of memory|OOM|memory limit)",
                r"(?i)(disk space|storage quota)",
                r"(?i)(resource exhausted|too many file descriptors)"
            ],
            "description": "Resource limit exceeded",
            "fix": "Increase available resources or optimize memory/disk usage",
            "severity": SeverityLevel.HIGH,
            "priority": 1
        }
    }
    
    def __init__(self, confidence_threshold: int = 50):
        self.confidence_threshold = confidence_threshold
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns for efficiency"""
        compiled = {}
        for category, info in self.PATTERNS.items():
            compiled[category] = {
                **info,
                "regex": [re.compile(pattern) for pattern in info["regex"]]
            }
        return compiled
    
    def analyze_test_results(self, test_results_file: str) -> Dict:
        """Parse test results from JSON file"""
        try:
            with open(test_results_file, 'r') as f:
                results = []
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        results.append(entry)
                    except json.JSONDecodeError:
                        continue
            return results
        except FileNotFoundError:
            print(f"❌ Test results file not found: {test_results_file}")
            return []
    
    def detect_root_causes(self, test_output: str) -> List[RootCause]:
        """Detect root causes from test output"""
        causes = []
        patterns_matched = {}
        
        for category, info in self.patterns.items():
            for regex_pattern in info["regex"]:
                if regex_pattern.search(test_output):
                    if category not in patterns_matched:
                        patterns_matched[category] = info
        
        for category, info in patterns_matched.items():
            confidence = min(100, 60 + len([r for r in info["regex"] if any(
                r.search(test_output) for r in info["regex"]
            )]) * 10)
            
            cause = RootCause(
                category=category.value,
                description=info["description"],
                pattern=info["regex"][0].pattern if info["regex"] else "",
                confidence=confidence,
                examples=[],
                suggested_fix=info["fix"],
                priority=info["priority"]
            )
            causes.append(cause)
        
        # Sort by priority and confidence
        causes.sort(key=lambda x: (x.priority, -x.confidence))
        return causes
    
    def extract_failed_tests(self, results: List[Dict]) -> List[Dict]:
        """Extract failed test information"""
        failed_tests = []
        
        for entry in results:
            if entry.get('Action') == 'fail' and entry.get('Test'):
                test = {
                    "name": entry.get('Test'),
                    "output": entry.get('Output', '')[:500],
                    "duration": entry.get('Elapsed', 0),
                    "package": entry.get('Test', '').split('/')[0]
                }
                failed_tests.append(test)
        
        return failed_tests
    
    def estimate_mttr(self, root_causes: List[RootCause]) -> int:
        """Estimate Mean Time To Recovery in minutes"""
        if not root_causes:
            return 30  # Default estimate
        
        mttr_map = {
            RootCauseCategory.TIMEOUT.value: 15,
            RootCauseCategory.NETWORK.value: 20,
            RootCauseCategory.IMPORT_ERROR.value: 10,
            RootCauseCategory.ASSERTION.value: 30,
            RootCauseCategory.PANIC.value: 45,
            RootCauseCategory.RESOURCE.value: 60,
            RootCauseCategory.CONFIG.value: 20,
            RootCauseCategory.UNKNOWN.value: 60,
        }
        
        # Use highest MTTR of detected causes
        mttr = max(mttr_map.get(cause.category, 30) for cause in root_causes)
        return mttr
    
    def calculate_impact_score(self, 
                               failed_count: int, 
                               total_count: int,
                               root_causes: List[RootCause]) -> int:
        """Calculate impact score (0-100)"""
        if total_count == 0:
            return 0
        
        failure_rate = (failed_count / total_count) * 100
        severity_multiplier = sum(1 for cause in root_causes if cause.priority < 2)
        
        impact = int(
            (failure_rate * 0.5) + 
            (severity_multiplier * 10) + 
            (min(failed_count * 5, 50))
        )
        
        return min(100, impact)
    
    def generate_suggestions(self, root_causes: List[RootCause]) -> List[Dict]:
        """Generate actionable fix suggestions"""
        suggestions = []
        seen = set()
        
        for cause in root_causes[:3]:  # Top 3 causes
            if cause.category in seen:
                continue
            seen.add(cause.category)
            
            suggestion = {
                "category": cause.category,
                "title": f"Fix {cause.description}",
                "description": cause.suggested_fix,
                "confidence": cause.confidence,
                "priority": cause.priority,
                "steps": self._get_fix_steps(cause.category)
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def _get_fix_steps(self, category: str) -> List[str]:
        """Get detailed fix steps for a category"""
        steps_map = {
            "timeout": [
                "1. Review test for blocking operations",
                "2. Increase test timeout duration",
                "3. Add async/await patterns for I/O",
                "4. Mock slow external services"
            ],
            "network": [
                "1. Check external service availability",
                "2. Add mock servers for integration tests",
                "3. Complete network tests locally first",
                "4. Use VPN if behind firewall"
            ],
            "import_error": [
                "1. Run 'go mod download' or 'pip install'",
                "2. Verify import path and package name",
                "3. Check go.mod or requirements.txt",
                "4. Clear module cache if outdated"
            ],
            "assertion": [
                "1. Review test assertions",
                "2. Verify test data setup",
                "3. Check expected vs actual values",
                "4. Run test locally with debugging"
            ],
            "panic": [
                "1. Add nil checks before operations",
                "2. Add error handling for failed calls",
                "3. Validate input parameters",
                "4. Review recent code changes"
            ],
            "resource": [
                "1. Check available memory/disk",
                "2. Profile test for memory leaks",
                "3. Optimize data structures",
                "4. Increase runner resources"
            ]
        }
        
        return steps_map.get(category, [
            "1. Review test execution logs",
            "2. Run test locally for debugging",
            "3. Check recent code changes",
            "4. Consult team for guidance"
        ])
    
    def generate_summary(self, test_results: List[Dict]) -> IncidentSummary:
        """Generate complete incident summary"""
        failed_tests = self.extract_failed_tests(test_results)
        
        # Aggregate output for analysis
        aggregated_output = "\n".join([
            test.get('Output', '') for test in test_results 
            if test.get('Action') == 'fail'
        ])
        
        # Detect root causes
        root_causes = self.detect_root_causes(aggregated_output)
        
        # Calculate metrics
        total_tests = len(test_results)
        failed_count = len(failed_tests)
        impact_score = self.calculate_impact_score(failed_count, total_tests, root_causes)
        mttr_estimate = self.estimate_mttr(root_causes)
        
        # Generate suggestions
        suggestions = self.generate_suggestions(root_causes)
        
        # Extract affected components
        affected_components = list(set([
            test.get('name', '').split('/')[0] for test in failed_tests
        ]))
        
        # Determine severity
        severity = "critical" if impact_score >= 80 else \
                  "high" if impact_score >= 60 else \
                  "medium" if impact_score >= 40 else "low"
        
        # Calculate overall confidence
        overall_confidence = int(sum(c.confidence for c in root_causes) / len(root_causes)) \
                            if root_causes else 0
        
        summary = IncidentSummary(
            timestamp=datetime.now().isoformat(),
            incident_id=f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=f"CI Pipeline Failure ({failed_count} tests failed)",
            description=f"Detected {len(root_causes)} root cause(s) affecting {len(affected_components)} component(s)",
            severity=severity,
            test_failures=failed_tests[:10],  # Top 10
            root_causes=[asdict(cause) for cause in root_causes[:3]],  # Top 3
            affected_components=affected_components[:5],  # Top 5
            suggested_fixes=suggestions,
            overall_confidence=overall_confidence,
            impact_score=impact_score,
            estimated_mttr_minutes=mttr_estimate
        )
        
        return summary
    
    def format_for_pr_comment(self, summary: IncidentSummary) -> str:
        """Format summary as markdown for PR comment"""
        comment = f"""## 🤖 AI-Powered Incident Summary

### 📊 Overview
- **Incident ID**: {summary['incident_id']}
- **Severity**: `{summary['severity'].upper()}`
- **Impact Score**: {summary['impact_score']}/100
- **Confidence**: {summary['overall_confidence']}%

### 🚨 Failures
- **Total Failed Tests**: {len(summary['test_failures'])}
- **Affected Components**: {', '.join(summary['affected_components'])}

### 🔍 Root Cause Analysis
"""
        
        if summary['root_causes']:
            for i, cause in enumerate(summary['root_causes'], 1):
                comment += f"""
**{i}. {cause['description']}**
- Category: `{cause['category']}`
- Confidence: {cause['confidence']}%
- Fix: {cause['suggested_fix']}
"""
        else:
            comment += "\nNo specific root causes detected. Please review test output manually.\n"
        
        comment += f"""
### 💡 Suggested Fixes
"""
        
        if summary['suggested_fixes']:
            for suggestion in summary['suggested_fixes']:
                comment += f"""
**{suggestion['title']}** (Confidence: {suggestion['confidence']}%)
```
{chr(10).join(suggestion['steps'])}
```
"""
        
        comment += f"""
### ⏱️ Estimated Recovery Time
- **MTTR**: ~{summary['estimated_mttr_minutes']} minutes

---
*Generated by 🤖 Self-Healing CI at {summary['timestamp']}*
"""
        
        return comment


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 incident_analyzer.py <test-result-json> [output-json]")
        print("\nExample:")
        print("  python3 incident_analyzer.py test-result.json incident-summary.json")
        sys.exit(1)
    
    test_result_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "incident-summary.json"
    
    # Run analysis
    analyzer = IncidentAnalyzer(confidence_threshold=50)
    
    print(f"📥 Analyzing: {test_result_file}")
    test_results = analyzer.analyze_test_results(test_result_file)
    
    if not test_results:
        print("❌ No test results found")
        sys.exit(1)
    
    print(f"📊 Processing {len(test_results)} test entries...")
    summary = analyzer.generate_summary(test_results)
    
    # Save JSON output
    with open(output_file, 'w') as f:
        json.dump(asdict(summary), f, indent=2)
    print(f"✅ Summary saved to: {output_file}")
    
    # Print PR comment format
    pr_comment = analyzer.format_for_pr_comment(asdict(summary))
    print("\n" + "=" * 80)
    print("PR COMMENT PREVIEW:")
    print("=" * 80)
    print(pr_comment)


if __name__ == "__main__":
    main()

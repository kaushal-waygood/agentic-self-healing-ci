#!/usr/bin/env python3
"""
Flaky Test Auto-Healer & Analyzer

Detects, tracks, and analyzes flaky tests to identify patterns and suggest fixes.

Features:
- Statistical detection of flaky test patterns
- Historical trend analysis
- Intelligent retry strategies
- Remediation recommendations
- Auto-fix suggestion generation

Usage:
    python3 flaky_test_healer.py --analyze <test-result.json>
    python3 flaky_test_healer.py --suggest-fixes <flaky-tests.json>
    python3 flaky_test_healer.py --generate-report
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import re
import statistics


@dataclass
class TestRun:
    """Single test execution record"""
    test_name: str
    status: str  # pass, fail
    duration: float
    timestamp: str
    output: str = ""
    package: str = ""


@dataclass
class FlakyTest:
    """Flaky test pattern"""
    test_name: str
    package: str
    failure_rate: float  # 0-1
    failure_count: int
    total_runs: int
    last_failure: str
    severity: str  # low, medium, high, critical
    root_causes: List[str] = field(default_factory=list)
    suggested_fixes: List[str] = field(default_factory=list)
    impact_score: int = 0
    
    def to_dict(self):
        return asdict(self)


class FlakyTestAnalyzer:
    """Analyzes and detects flaky test patterns"""
    
    # Flakiness thresholds
    FLAKY_THRESHOLD = 0.1  # 10% failure rate = flaky
    CRITICAL_THRESHOLD = 0.5  # 50% failure rate = critical
    
    # Common flakiness patterns
    FLAKY_PATTERNS = {
        "timing": {
            "regex": [
                r"(?i)(sleep|wait|delay|timeout|timing)",
                r"(?i)(race condition|concurrent|async)",
            ],
            "cause": "Timing-sensitive test logic",
            "fix": "Add proper wait mechanisms, use condition variables"
        },
        "external_service": {
            "regex": [
                r"(?i)(network|http|api|external|mock|stub)",
                r"(?i)(database|connection|pool)",
            ],
            "cause": "Dependency on external services",
            "fix": "Mock external dependencies, add retry logic"
        },
        "shared_state": {
            "regex": [
                r"(?i)(shared|global|singleton|static)",
                r"(?i)(cache|state|instance variable)",
            ],
            "cause": "Test pollution or shared mutable state",
            "fix": "Isolate tests, clean up between runs"
        },
        "random_data": {
            "regex": [
                r"(?i)(random|seed|uuid|guid)",
                r"(?i)(mock_random|stub_random)",
            ],
            "cause": "Non-deterministic test data",
            "fix": "Use fixed seeds, deterministic test data"
        },
        "order_dependent": {
            "regex": [
                r"(?i)(order|sequence|depend|fixture)",
                r"(?i)(setup|teardown|before|after)",
            ],
            "cause": "Dependency on test execution order",
            "fix": "Make tests independent, avoid order assumptions"
        },
        "resource_limit": {
            "regex": [
                r"(?i)(memory|cpu|disk|resource|limit|quota)",
                r"(?i)(thread|goroutine|process)",
            ],
            "cause": "Resource constraints or leaks",
            "fix": "Profile for leaks, increase resources"
        }
    }
    
    def __init__(self):
        self.patterns = self._compile_patterns()
        self.test_history: Dict[str, List[TestRun]] = defaultdict(list)
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns"""
        compiled = {}
        for category, info in self.FLAKY_PATTERNS.items():
            compiled[category] = {
                **info,
                "regex": [re.compile(p) for p in info["regex"]]
            }
        return compiled
    
    def load_test_results(self, results_file: str) -> List[TestRun]:
        """Load test results from JSON file"""
        runs = []
        try:
            with open(results_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('Test'):
                            run = TestRun(
                                test_name=entry.get('Test', ''),
                                status='pass' if entry.get('Action') == 'pass' else 'fail',
                                duration=entry.get('Elapsed', 0),
                                timestamp=datetime.now().isoformat(),
                                output=entry.get('Output', ''),
                                package=entry.get('Test', '').split('/')[0] if entry.get('Test') else ''
                            )
                            runs.append(run)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"❌ File not found: {results_file}")
            return []
        
        return runs
    
    def load_test_history(self, history_file: str) -> Dict[str, List[TestRun]]:
        """Load historical test execution data"""
        history = defaultdict(list)
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    for test_name, runs in data.items():
                        for run in runs:
                            history[test_name].append(TestRun(**run))
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return history
    
    def detect_flaky_tests(self, runs: List[TestRun], 
                          threshold: float = FLAKY_THRESHOLD) -> List[FlakyTest]:
        """Detect flaky tests from current run"""
        flaky_tests = []
        test_groups = defaultdict(list)
        
        # Group runs by test name
        for run in runs:
            test_groups[run.test_name].append(run)
        
        # Analyze each test
        for test_name, test_runs in test_groups.items():
            if len(test_runs) < 2:
                continue  # Need multiple runs to detect flakiness
            
            failure_count = sum(1 for r in test_runs if r.status == 'fail')
            total_runs = len(test_runs)
            failure_rate = failure_count / total_runs
            
            if failure_rate >= threshold:
                # Determine severity
                if failure_rate >= self.CRITICAL_THRESHOLD:
                    severity = "critical"
                elif failure_rate >= 0.3:
                    severity = "high"
                elif failure_rate >= threshold:
                    severity = "medium"
                else:
                    severity = "low"
                
                # Detect patterns
                aggregated_output = "\n".join([r.output for r in test_runs if r.output])
                patterns = self._detect_patterns(aggregated_output)
                fixes = self._suggest_fixes(patterns)
                
                # Calculate impact
                impact = self._calculate_impact(failure_rate, severity, test_name)
                
                flaky = FlakyTest(
                    test_name=test_name,
                    package=test_runs[0].package,
                    failure_rate=failure_rate,
                    failure_count=failure_count,
                    total_runs=total_runs,
                    last_failure=max([r.timestamp for r in test_runs if r.status == 'fail'],
                                    default=datetime.now().isoformat()),
                    severity=severity,
                    root_causes=patterns,
                    suggested_fixes=fixes,
                    impact_score=impact
                )
                flaky_tests.append(flaky)
        
        # Sort by impact
        flaky_tests.sort(key=lambda x: -x.impact_score)
        return flaky_tests
    
    def _detect_patterns(self, output: str) -> List[str]:
        """Detect flaky patterns from test output"""
        patterns = []
        
        for category, info in self.patterns.items():
            for regex in info["regex"]:
                if regex.search(output):
                    patterns.append(f"{category}: {info['cause']}")
                    break
        
        return patterns if patterns else ["Unknown pattern"]
    
    def _suggest_fixes(self, patterns: List[str]) -> List[str]:
        """Generate fix suggestions based on detected patterns"""
        fixes = set()
        
        for category, info in self.FLAKY_PATTERNS.items():
            for pattern in patterns:
                if category.lower() in pattern.lower():
                    fixes.add(info['fix'])
        
        # Add generic fixes
        generic_fixes = [
            "✅ Add comprehensive error handling and logging",
            "✅ Increase test timeout if performing I/O operations",
            "✅ Ensure test isolation (no shared state)",
            "✅ Run test locally multiple times to reproduce",
        ]
        
        return list(fixes) + generic_fixes[:2]
    
    def _calculate_impact(self, failure_rate: float, severity: str, test_name: str) -> int:
        """Calculate impact score (0-100)"""
        severity_score = {
            "critical": 100,
            "high": 75,
            "medium": 50,
            "low": 25
        }.get(severity, 25)
        
        rate_score = int(failure_rate * 100)
        name_length_factor = 1.0 if len(test_name) < 30 else 0.8
        
        impact = int((severity_score * 0.6 + rate_score * 0.4) * name_length_factor)
        return min(100, impact)
    
    def analyze_stability_trend(self, 
                                test_name: str,
                                history: Dict[str, List[TestRun]],
                                days: int = 7) -> Dict:
        """Analyze stability trend over time"""
        if test_name not in history:
            return {"status": "no_data", "trend": "unknown"}
        
        runs = history[test_name]
        recent = [r for r in runs if (
            datetime.now() - datetime.fromisoformat(r.timestamp)
        ).days <= days]
        
        if not recent:
            return {"status": "no_recent_data", "trend": "unknown"}
        
        failure_count = sum(1 for r in recent if r.status == 'fail')
        total = len(recent)
        current_rate = failure_count / total if total > 0 else 0
        
        # Compare to earlier period
        older = [r for r in runs if (
            datetime.now() - datetime.fromisoformat(r.timestamp)
        ).days > days]
        
        if not older:
            return {
                "status": "improving" if failure_count == 0 else "degrading",
                "trend": "stable",
                "current_rate": current_rate
            }
        
        older_failure_count = sum(1 for r in older if r.status == 'fail')
        older_rate = older_failure_count / len(older) if older else 0
        
        if current_rate < older_rate:
            trend = "improving"
        elif current_rate > older_rate:
            trend = "degrading"
        else:
            trend = "stable"
        
        return {
            "status": "tracked",
            "trend": trend,
            "current_rate": current_rate,
            "previous_rate": older_rate,
            "recent_runs": total
        }
    
    def generate_report(self, flaky_tests: List[FlakyTest], 
                       history: Optional[Dict] = None) -> Dict:
        """Generate comprehensive flaky test report"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_flaky": len(flaky_tests),
                "critical": sum(1 for t in flaky_tests if t.severity == "critical"),
                "high": sum(1 for t in flaky_tests if t.severity == "high"),
                "medium": sum(1 for t in flaky_tests if t.severity == "medium"),
                "low": sum(1 for t in flaky_tests if t.severity == "low"),
            },
            "flaky_tests": [t.to_dict() for t in flaky_tests[:20]],  # Top 20
            "trends": {}
        }
        
        # Add trend analysis if history provided
        if history:
            for test in flaky_tests[:10]:
                trend = self.analyze_stability_trend(
                    test.test_name, 
                    history, 
                    days=7
                )
                report["trends"][test.test_name] = trend
        
        return report
    
    def format_report_markdown(self, report: Dict) -> str:
        """Format report as markdown"""
        md = f"""# 🔴 Flaky Test Analysis Report

**Generated**: {report['timestamp']}

## Summary
- **Total Flaky Tests**: {report['summary']['total_flaky']}
  - 🔥 Critical: {report['summary']['critical']}
  - 🔴 High: {report['summary']['high']}
  - 🟡 Medium: {report['summary']['medium']}
  - 🟢 Low: {report['summary']['low']}

## Flaky Tests

"""
        
        for test in report.get('flaky_tests', [])[:10]:
            severity_emoji = {
                "critical": "🔥",
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(test['severity'], "❓")
            
            md += f"""
### {severity_emoji} {test['test_name']}

- **Package**: `{test['package']}`
- **Failure Rate**: {test['failure_rate']*100:.1f}% ({test['failure_count']}/{test['total_runs']})
- **Impact Score**: {test['impact_score']}/100
- **Last Failure**: {test['last_failure']}

**Root Causes**:
"""
            for cause in test.get('root_causes', []):
                md += f"- {cause}\n"
            
            md += "\n**Suggested Fixes**:\n"
            for fix in test.get('suggested_fixes', [])[:3]:
                md += f"- {fix}\n"
            
            # Add trend if available
            if test['test_name'] in report.get('trends', {}):
                trend = report['trends'][test['test_name']]
                trend_indicator = {
                    "improving": "📈",
                    "degrading": "📉",
                    "stable": "➡️"
                }.get(trend.get('trend'), "❓")
                md += f"\n**Trend**: {trend_indicator} {trend['trend']}\n"
        
        return md


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Flaky Test Auto-Healer & Analyzer"
    )
    
    parser.add_argument('--analyze', type=str, 
                       help='Analyze test results file')
    parser.add_argument('--history', type=str, default='.github/metrics/test-history.json',
                       help='Path to test history file')
    parser.add_argument('--output', type=str, default='flaky-tests.json',
                       help='Output file for flaky tests')
    parser.add_argument('--threshold', type=float, default=0.1,
                       help='Flakiness threshold (0-1)')
    
    args = parser.parse_args()
    
    analyzer = FlakyTestAnalyzer()
    
    if args.analyze:
        print(f"📊 Analyzing: {args.analyze}")
        
        # Load current results
        runs = analyzer.load_test_results(args.analyze)
        if not runs:
            print("❌ No test results found")
            sys.exit(1)
        
        # Detect flaky tests
        flaky_tests = analyzer.detect_flaky_tests(runs, args.threshold)
        
        # Load history for trend analysis
        history = analyzer.load_test_history(args.history)
        
        # Generate report
        report = analyzer.generate_report(flaky_tests, history)
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ Results saved to: {args.output}")
        
        # Print markdown report
        md_report = analyzer.format_report_markdown(report)
        print("\n" + md_report)
        
        # Update history
        os.makedirs(os.path.dirname(args.history), exist_ok=True)
        with open(args.history, 'w') as f:
            history_data = {}
            for run in runs:
                if run.test_name not in history_data:
                    history_data[run.test_name] = []
                history_data[run.test_name].append(asdict(run))
            json.dump(history_data, f, indent=2)
        
        # Summary
        if flaky_tests:
            print(f"\n🚨 Found {len(flaky_tests)} flaky test(s)")
            print("\nTop 3 by impact:")
            for i, test in enumerate(flaky_tests[:3], 1):
                print(f"  {i}. {test.test_name} ({test.severity}: {test.impact_score})")
        else:
            print("\n✅ No flaky tests detected!")


if __name__ == "__main__":
    main()

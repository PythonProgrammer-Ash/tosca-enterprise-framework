#!/usr/bin/env python3
"""
JIRA/Xray Integration Script for Tosca Test Results
Auto-creates defects for failed tests and updates test execution status
"""

import argparse
import json
import requests
import sys
from datetime import datetime
from requests.auth import HTTPBasicAuth


class JiraXrayIntegration:
    """Handler for JIRA and Xray API integration"""

    def __init__(self, jira_url, username, password, project_key):
        self.jira_url = jira_url.rstrip("/")
        self.auth = HTTPBasicAuth(username, password)
        self.project_key = project_key
        self.headers = {"Content-Type": "application/json"}

    def create_test_execution(self, build_number, summary_data):
        """Create Xray Test Execution"""
        endpoint = f"{self.jira_url}/rest/api/2/issue"

        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": f"Tosca Test Execution - Build {build_number}",
                "description": self._format_execution_description(summary_data),
                "issuetype": {"name": "Test Execution"},
                "labels": ["Automation", "Tosca", f"Build-{build_number}"],
            }
        }

        try:
            response = requests.post(
                endpoint, headers=self.headers, auth=self.auth, json=payload
            )
            response.raise_for_status()
            execution_key = response.json()["key"]
            print(f"✅ Created Test Execution: {execution_key}")
            return execution_key
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create test execution: {e}")
            if hasattr(e.response, "text"):
                print(f"Response: {e.response.text}")
            return None

    def create_defect(self, test_result, build_number):
        """Create a defect for a failed test"""
        endpoint = f"{self.jira_url}/rest/api/2/issue"

        test_name = test_result.get("name", "Unknown Test")
        error_msg = test_result.get("error_message", "No error details")
        screenshots = test_result.get("screenshots", [])

        # Determine priority based on test criticality
        priority = self._determine_priority(test_result)

        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": f"[Automation] {test_name} - Failed",
                "description": self._format_defect_description(
                    test_result, build_number
                ),
                "issuetype": {"name": "Bug"},
                "priority": {"name": priority},
                "labels": [
                    "Automation",
                    "Tosca",
                    "TestFailure",
                    f"Build-{build_number}",
                ],
                "components": [{"name": test_result.get("component", "General")}],
            }
        }

        try:
            response = requests.post(
                endpoint, headers=self.headers, auth=self.auth, json=payload
            )
            response.raise_for_status()
            defect_key = response.json()["key"]
            print(f"  🐛 Created defect: {defect_key} for {test_name}")

            # Attach screenshots
            if screenshots:
                self.attach_files(defect_key, screenshots)

            return defect_key
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Failed to create defect for {test_name}: {e}")
            return None

    def attach_files(self, issue_key, file_paths):
        """Attach files to JIRA issue"""
        endpoint = f"{self.jira_url}/rest/api/2/issue/{issue_key}/attachments"
        headers = {"X-Atlassian-Token": "no-check"}

        for file_path in file_paths:
            try:
                with open(file_path, "rb") as f:
                    files = {"file": f}
                    response = requests.post(
                        endpoint, headers=headers, auth=self.auth, files=files
                    )
                    response.raise_for_status()
                    print(f"    📎 Attached: {file_path}")
            except Exception as e:
                print(f"    ⚠️ Failed to attach {file_path}: {e}")

    def update_test_status(self, test_execution_key, test_key, status):
        """Update test status in Xray"""
        # Xray REST API endpoint for updating test status
        endpoint = (
            f"{self.jira_url}/rest/raven/1.0/api/testexec/{test_execution_key}/test"
        )

        status_mapping = {
            "Passed": "PASS",
            "Failed": "FAIL",
            "Skipped": "TODO",
            "Blocked": "ABORTED",
        }

        payload = {"testKey": test_key, "status": status_mapping.get(status, "FAIL")}

        try:
            response = requests.post(
                endpoint, headers=self.headers, auth=self.auth, json=payload
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️ Failed to update status for {test_key}: {e}")
            return False

    def _format_execution_description(self, summary):
        """Format test execution description"""
        return f"""
h2. Test Execution Summary

*Total Tests:* {summary.get('total', 0)}
*Passed:* {summary.get('passed', 0)} ({summary.get('passRate', 0)}%)
*Failed:* {summary.get('failed', 0)}
*Skipped:* {summary.get('skipped', 0)}

*Execution Time:* {summary.get('duration', 'N/A')}
*Environment:* {summary.get('environment', 'QA')}
*Executed:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

----
_This execution was automated via Tosca CI/CD pipeline_
"""

    def _format_defect_description(self, test_result, build_number):
        """Format defect description"""
        return f"""
h2. Test Failure Details

*Test Name:* {test_result.get('name', 'Unknown')}
*Build Number:* {build_number}
*Execution Time:* {test_result.get('execution_time', 'N/A')}
*Environment:* {test_result.get('environment', 'QA')}

h3. Error Message
{{code}}
{test_result.get('error_message', 'No error details available')}
{{code}}

h3. Steps to Reproduce
{test_result.get('steps', 'See attached test case details')}

h3. Expected Result
{test_result.get('expected_result', 'Test should pass')}

h3. Actual Result
Test failed with the error shown above

h3. Additional Information
* Browser: {test_result.get('browser', 'Chrome')}
* Test Suite: {test_result.get('suite', 'Regression')}
* Module: {test_result.get('module', 'N/A')}

----
_This defect was automatically created by Tosca automation_
"""

    def _determine_priority(self, test_result):
        """Determine defect priority based on test attributes"""
        # Check if test is marked as critical
        if test_result.get("critical", False):
            return "Critical"

        # Check test suite
        suite = test_result.get("suite", "").lower()
        if "smoke" in suite or "critical" in suite:
            return "High"

        return "Medium"

    def process_results(self, results_data, build_number):
        """Main method to process all test results"""
        print("\n" + "=" * 60)
        print("  Processing Results for JIRA/Xray")
        print("=" * 60)

        # Create Test Execution
        execution_key = self.create_test_execution(build_number, results_data)

        if not execution_key:
            print("⚠️ Continuing without test execution...")

        # Process failed tests
        failed_tests = [
            t
            for t in results_data.get("test_results", [])
            if t.get("status") == "Failed"
        ]

        print(f"\n🐛 Creating defects for {len(failed_tests)} failed tests...")

        defects_created = 0
        for test in failed_tests:
            if self.create_defect(test, build_number):
                defects_created += 1

            # Update test status in Xray if execution exists
            if execution_key:
                test_key = test.get("xray_test_key")
                if test_key:
                    self.update_test_status(execution_key, test_key, test.get("status"))

        # Update passed tests
        passed_tests = [
            t
            for t in results_data.get("test_results", [])
            if t.get("status") == "Passed"
        ]

        if execution_key:
            print(f"\n✅ Updating {len(passed_tests)} passed tests in Xray...")
            for test in passed_tests:
                test_key = test.get("xray_test_key")
                if test_key:
                    self.update_test_status(execution_key, test_key, "Passed")

        # Summary
        print("\n" + "=" * 60)
        print(f"  SUMMARY")
        print("=" * 60)
        print(f"Test Execution: {execution_key if execution_key else 'Not created'}")
        print(f"Defects Created: {defects_created}/{len(failed_tests)}")
        print(f"Tests Updated in Xray: {len(passed_tests) + len(failed_tests)}")
        print("=" * 60 + "\n")

        return True


def load_results(results_file):
    """Load test results from JSON file"""
    try:
        with open(results_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load results file: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Integrate Tosca results with JIRA/Xray"
    )
    parser.add_argument("--results", required=True, help="Path to results JSON file")
    parser.add_argument("--jira-url", required=True, help="JIRA instance URL")
    parser.add_argument("--username", required=True, help="JIRA username")
    parser.add_argument("--password", required=True, help="JIRA password/token")
    parser.add_argument("--project", required=True, help="JIRA project key")
    parser.add_argument("--build-number", required=True, help="Build number")

    args = parser.parse_args()

    # Load results
    results = load_results(args.results)

    # Initialize JIRA integration
    jira = JiraXrayIntegration(
        args.jira_url, args.username, args.password, args.project
    )

    # Process results
    success = jira.process_results(results, args.build_number)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
qTest Integration Script for Tosca Test Results
Publishes test execution results to qTest Manager
"""

import argparse
import json
import requests
import sys
from datetime import datetime
from pathlib import Path


class QTestIntegration:
    """Handler for qTest API integration"""

    def __init__(self, api_url, token, project_id):
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.project_id = project_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def create_test_cycle(self, cycle_name, description=""):
        """Create a new test cycle in qTest"""
        endpoint = f"{self.api_url}/projects/{self.project_id}/test-cycles"

        payload = {
            "name": cycle_name,
            "description": description,
            "start_date": datetime.now().isoformat(),
            "end_date": datetime.now().isoformat(),
        }

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            cycle_data = response.json()
            print(f"✅ Created test cycle: {cycle_name} (ID: {cycle_data['id']})")
            return cycle_data["id"]
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create test cycle: {e}")
            return None

    def create_test_run(self, cycle_id, test_case_id, test_name):
        """Create a test run within a cycle"""
        endpoint = f"{self.api_url}/projects/{self.project_id}/test-runs"

        payload = {
            "name": test_name,
            "test_case": {"id": test_case_id},
            "test_cycle": {"id": cycle_id},
        }

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()["id"]
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Failed to create test run for {test_name}: {e}")
            return None

    def update_test_run_status(
        self, run_id, status, execution_time, error_message="", attachments=None
    ):
        """Update test run with execution results"""
        endpoint = f"{self.api_url}/projects/{self.project_id}/test-runs/{run_id}/auto-test-logs"

        # Map Tosca status to qTest status
        status_mapping = {
            "Passed": "PASSED",
            "Failed": "FAILED",
            "Skipped": "INCOMPLETE",
            "Blocked": "BLOCKED",
        }

        qtest_status = status_mapping.get(status, "FAILED")

        payload = {
            "exe_start_date": datetime.now().isoformat(),
            "exe_end_date": datetime.now().isoformat(),
            "status": qtest_status,
            "note": error_message if error_message else "Test executed successfully",
            "execution_time": execution_time,
        }

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()

            # Upload attachments if provided
            if attachments and qtest_status == "FAILED":
                self.upload_attachments(run_id, attachments)

            return True
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Failed to update test run {run_id}: {e}")
            return False

    def upload_attachments(self, run_id, attachments):
        """Upload screenshots and logs to test run"""
        endpoint = (
            f"{self.api_url}/projects/{self.project_id}/test-runs/{run_id}/attachments"
        )

        for attachment_path in attachments:
            if not Path(attachment_path).exists():
                continue

            try:
                with open(attachment_path, "rb") as f:
                    files = {"file": f}
                    # Remove Content-Type from headers for multipart upload
                    headers = {"Authorization": self.headers["Authorization"]}
                    response = requests.post(endpoint, headers=headers, files=files)
                    response.raise_for_status()
                    print(f"  📎 Uploaded attachment: {Path(attachment_path).name}")
            except Exception as e:
                print(f"  ⚠️ Failed to upload {attachment_path}: {e}")

    def publish_results(self, results_data, cycle_name):
        """Main method to publish all test results"""
        print("\n" + "=" * 60)
        print("  Publishing Results to qTest")
        print("=" * 60)

        # Create test cycle
        cycle_id = self.create_test_cycle(
            cycle_name,
            f"Automated execution via Tosca CI/CD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        )

        if not cycle_id:
            print("❌ Cannot proceed without a test cycle")
            return False

        # Process each test result
        total = len(results_data.get("test_results", []))
        successful_updates = 0

        print(f"\n📊 Processing {total} test results...")

        for idx, test in enumerate(results_data.get("test_results", []), 1):
            test_name = test.get("name", "Unknown Test")
            test_case_id = test.get("test_case_id")  # Must be mapped from Tosca
            status = test.get("status", "Failed")
            duration = test.get("duration", 0)
            error = test.get("error_message", "")
            screenshots = test.get("screenshots", [])

            print(f"\n[{idx}/{total}] {test_name}")

            if not test_case_id:
                print("  ⚠️ No qTest test case ID mapped - skipping")
                continue

            # Create test run
            run_id = self.create_test_run(cycle_id, test_case_id, test_name)

            if run_id:
                # Update with results
                if self.update_test_run_status(
                    run_id, status, duration, error, screenshots
                ):
                    successful_updates += 1
                    print(f"  ✅ Updated test run (Status: {status})")

        # Summary
        print("\n" + "=" * 60)
        print(f"  SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Successfully Updated: {successful_updates}")
        print(f"Failed: {total - successful_updates}")
        print(
            f"Success Rate: {(successful_updates/total*100):.1f}%"
            if total > 0
            else "N/A"
        )
        print("=" * 60 + "\n")

        return successful_updates == total


def load_results(results_file):
    """Load test results from JSON file"""
    try:
        with open(results_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load results file: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Publish Tosca results to qTest")
    parser.add_argument("--results", required=True, help="Path to results JSON file")
    parser.add_argument("--api-url", required=True, help="qTest API URL")
    parser.add_argument("--token", required=True, help="qTest API token")
    parser.add_argument("--project-id", required=True, help="qTest project ID")
    parser.add_argument("--test-cycle", required=True, help="Test cycle name")

    args = parser.parse_args()

    # Load results
    results = load_results(args.results)

    # Initialize qTest integration
    qtest = QTestIntegration(args.api_url, args.token, args.project_id)

    # Publish results
    success = qtest.publish_results(results, args.test_cycle)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

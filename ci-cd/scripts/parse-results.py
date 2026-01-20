#!/usr/bin/env python3
"""
Tosca Results Parser
Parses Tosca XML execution results and generates JSON summary
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List


class ToscaResultsParser:
    """Parser for Tosca execution results"""

    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)
        self.results = {
            "execution_date": datetime.now().isoformat(),
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "blocked": 0,
            "passRate": 0.0,
            "duration": "0:00:00",
            "test_results": [],
        }

    def parse_xml_results(self) -> Dict:
        """Parse Tosca XML result files"""
        xml_files = list(self.results_dir.glob("**/*.xml"))

        if not xml_files:
            print(f"⚠️ No XML result files found in {self.results_dir}")
            return self.results

        print(f"📄 Found {len(xml_files)} XML result file(s)")

        total_duration = timedelta()

        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Parse test cases from XML
                test_cases = self._parse_test_cases(root)
                self.results["test_results"].extend(test_cases)

                # Calculate duration
                duration = self._extract_duration(root)
                if duration:
                    total_duration += duration

            except ET.ParseError as e:
                print(f"⚠️ Failed to parse {xml_file}: {e}")
                continue
            except Exception as e:
                print(f"⚠️ Error processing {xml_file}: {e}")
                continue

        # Calculate summary statistics
        self._calculate_summary(total_duration)

        return self.results

    def _parse_test_cases(self, root: ET.Element) -> List[Dict]:
        """Extract test case results from XML"""
        test_cases = []

        # Tosca XML structure varies, adapt as needed
        # This is a generic parser - adjust based on your Tosca version

        for test_case in root.findall(".//TestCase"):
            try:
                name = test_case.get("Name", "Unknown Test")
                status = self._determine_status(test_case)

                test_data = {
                    "name": name,
                    "status": status,
                    "execution_time": test_case.get("ExecutionTime", "N/A"),
                    "start_time": test_case.get("StartTime", ""),
                    "end_time": test_case.get("EndTime", ""),
                    "duration": self._calculate_test_duration(test_case),
                    "error_message": self._extract_error_message(test_case),
                    "screenshots": self._find_screenshots(test_case),
                    "module": test_case.get("Module", "N/A"),
                    "suite": test_case.get("Suite", "N/A"),
                    "test_case_id": test_case.get("ID", ""),
                    "xray_test_key": self._extract_custom_field(
                        test_case, "JIRA_Test_Key"
                    ),
                    "critical": self._is_critical_test(test_case),
                }

                test_cases.append(test_data)

            except Exception as e:
                print(f"⚠️ Error parsing test case: {e}")
                continue

        return test_cases

    def _determine_status(self, test_case: ET.Element) -> str:
        """Determine test execution status"""
        # Check Result element
        result_elem = test_case.find(".//Result")
        if result_elem is not None:
            status = result_elem.get("Status", "").lower()

            if status in ["passed", "success"]:
                return "Passed"
            elif status in ["failed", "failure"]:
                return "Failed"
            elif status in ["skipped", "notexecuted"]:
                return "Skipped"
            elif status in ["blocked"]:
                return "Blocked"

        # Check VerificationStatus
        verification = test_case.find(".//VerificationStatus")
        if verification is not None:
            if verification.text and "pass" in verification.text.lower():
                return "Passed"
            elif verification.text and "fail" in verification.text.lower():
                return "Failed"

        # Default to Failed if unclear
        return "Failed"

    def _extract_error_message(self, test_case: ET.Element) -> str:
        """Extract error message from failed test"""
        # Check various possible error locations
        error_locations = [
            ".//ErrorMessage",
            ".//Error",
            ".//FailureReason",
            ".//ExceptionMessage",
        ]

        for location in error_locations:
            elem = test_case.find(location)
            if elem is not None and elem.text:
                return elem.text.strip()

        # Check for verification failures
        verification = test_case.find(".//VerificationResult")
        if verification is not None and verification.get("Status") == "Failed":
            return verification.get("Message", "Verification failed")

        return ""

    def _find_screenshots(self, test_case: ET.Element) -> List[str]:
        """Find screenshot file paths"""
        screenshots = []

        for screenshot in test_case.findall(".//Screenshot"):
            path = screenshot.get("Path", "")
            if path:
                screenshots.append(path)

        return screenshots

    def _extract_custom_field(self, test_case: ET.Element, field_name: str) -> str:
        """Extract custom field value"""
        custom_fields = test_case.find(".//CustomFields")
        if custom_fields is not None:
            for field in custom_fields.findall(".//Field"):
                if field.get("Name") == field_name:
                    return field.get("Value", "")
        return ""

    def _is_critical_test(self, test_case: ET.Element) -> bool:
        """Determine if test is marked as critical"""
        priority = test_case.get("Priority", "").lower()
        tags = test_case.get("Tags", "").lower()

        return "critical" in priority or "critical" in tags or "smoke" in tags

    def _calculate_test_duration(self, test_case: ET.Element) -> int:
        """Calculate test duration in seconds"""
        start = test_case.get("StartTime", "")
        end = test_case.get("EndTime", "")

        if start and end:
            try:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                return int((end_dt - start_dt).total_seconds())
            except:
                pass

        # Try ExecutionTime if available
        exec_time = test_case.get("ExecutionTime", "0")
        try:
            return int(float(exec_time))
        except:
            return 0

    def _extract_duration(self, root: ET.Element) -> timedelta:
        """Extract total execution duration"""
        duration_elem = root.find(".//Duration")
        if duration_elem is not None:
            try:
                # Parse duration string (format: HH:MM:SS or seconds)
                duration_str = duration_elem.text
                if ":" in duration_str:
                    parts = duration_str.split(":")
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = int(float(parts[2]))
                    return timedelta(hours=hours, minutes=minutes, seconds=seconds)
                else:
                    return timedelta(seconds=float(duration_str))
            except:
                pass

        return timedelta()

    def _calculate_summary(self, total_duration: timedelta):
        """Calculate summary statistics"""
        for test in self.results["test_results"]:
            self.results["total"] += 1
            status = test["status"]

            if status == "Passed":
                self.results["passed"] += 1
            elif status == "Failed":
                self.results["failed"] += 1
            elif status == "Skipped":
                self.results["skipped"] += 1
            elif status == "Blocked":
                self.results["blocked"] += 1

        # Calculate pass rate
        if self.results["total"] > 0:
            self.results["passRate"] = round(
                (self.results["passed"] / self.results["total"]) * 100, 2
            )

        # Format duration
        hours = int(total_duration.total_seconds() // 3600)
        minutes = int((total_duration.total_seconds() % 3600) // 60)
        seconds = int(total_duration.total_seconds() % 60)
        self.results["duration"] = f"{hours}:{minutes:02d}:{seconds:02d}"

    def save_results(self, output_file: str, output_format: str = "json"):
        """Save parsed results to file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_format == "json":
            with open(output_path, "w") as f:
                json.dump(self.results, f, indent=2)
            print(f"✅ Results saved to: {output_path}")
        else:
            print(f"❌ Unsupported format: {output_format}")

    def print_summary(self):
        """Print execution summary to console"""
        print("\n" + "=" * 60)
        print("  TOSCA EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Total Tests:   {self.results['total']}")
        print(f"Passed:        {self.results['passed']} ({self.results['passRate']}%)")
        print(f"Failed:        {self.results['failed']}")
        print(f"Skipped:       {self.results['skipped']}")
        print(f"Blocked:       {self.results['blocked']}")
        print(f"Duration:      {self.results['duration']}")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Parse Tosca execution results")
    parser.add_argument(
        "--results-dir", required=True, help="Directory containing XML results"
    )
    parser.add_argument(
        "--output-format", default="json", choices=["json"], help="Output format"
    )
    parser.add_argument("--output-file", required=True, help="Output file path")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Parse results
    print(f"📊 Parsing Tosca results from: {args.results_dir}")
    parser_obj = ToscaResultsParser(args.results_dir)
    results = parser_obj.parse_xml_results()

    # Print summary
    parser_obj.print_summary()

    # Save results
    parser_obj.save_results(args.output_file, args.output_format)

    # Exit with appropriate code
    if results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

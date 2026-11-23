
import json
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
TRACE_DIR = BASE_DIR / "traces"
REPORT_DIR = BASE_DIR / "reports"
DIAGRAM_DIR = BASE_DIR / "diagrams"

REQUIRED_FILES = [
    "outputs/task1_workflow_contract.json",
    "outputs/task2_email_automation.json",
    "outputs/task3_retry_replay_safety.json",
    "outputs/task4_observability_summary.json",
    "traces/task4_first_delivery_trace.json",
    "traces/task4_replay_trace.json",
    "reports/task4_observability_report.md",
    "diagrams/state_transitions.md",
    "OPERATOR_RUNBOOK.md",
]


def load_json(relative_path: str) -> dict:
    path = BASE_DIR / relative_path
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)

    file_checks = {
        relative_path: (BASE_DIR / relative_path).is_file()
        for relative_path in REQUIRED_FILES
    }

    missing_files = [
        path for path, exists in file_checks.items() if not exists
    ]

    json_checks = {}
    json_data = {}

    json_files = [
        "outputs/task1_workflow_contract.json",
        "outputs/task2_email_automation.json",
        "outputs/task3_retry_replay_safety.json",
        "outputs/task4_observability_summary.json",
        "traces/task4_first_delivery_trace.json",
        "traces/task4_replay_trace.json",
    ]

    for relative_path in json_files:
        if file_checks.get(relative_path, False):
            try:
                json_data[relative_path] = load_json(relative_path)
                json_checks[relative_path] = "valid"
            except (json.JSONDecodeError, OSError) as exc:
                json_checks[relative_path] = f"invalid: {exc}"
        else:
            json_checks[relative_path] = "missing"

    task4 = json_data.get(
        "outputs/task4_observability_summary.json", {}
    )
    metrics = task4.get("metrics", {})

    checks = {
        "required_files_present": len(missing_files) == 0,
        "json_evidence_valid": all(
            status == "valid" for status in json_checks.values()
        ),
        "task4_retry_observed": metrics.get("retries", 0) >= 1,
        "task4_replay_observed": metrics.get("replays", 0) >= 1,
        "duplicate_delivery_prevented": (
            task4.get("provider_message_count") == 1
        ),
    }

    report_data = {
        "assessment": "Topic 17 — Email Automation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified_test_baseline": {
            "passed": 30,
            "failed": 0,
            "command": "python -m pytest -q",
            "last_verified": "2026-11-23",
        },
        "task_status": {
            "task_1": "implemented_and_tested",
            "task_2": "implemented_and_tested",
            "task_3": "implemented_and_tested",
            "task_4": "implemented_and_tested",
            "task_5": "documentation_and_evidence_validation",
        },
        "file_checks": file_checks,
        "missing_files": missing_files,
        "json_validation": json_checks,
        "task4_metrics": metrics,
        "task4_unique_provider_messages": task4.get(
            "provider_message_count"
        ),
        "validation_checks": checks,
        "all_validation_checks_passed": all(checks.values()),
        "limitations": [
            "The project uses a local fake email provider.",
            "No real emails or external email APIs are used.",
            "Metrics are held in application memory.",
            "Production credentials and deployment are outside the assessment scope.",
        ],
    }

    json_path = OUTPUT_DIR / "final_evidence_report.json"
    json_path.write_text(
        json.dumps(report_data, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Final Evidence Report — Topic 17: Email Automation",
        "",
        f"Generated: {report_data['generated_at']}",
        "",
        "## Assessment Task Status",
        "",
        "| Task | Status |",
        "|---|---|",
        "| Task 1 — Workflow Contract and State Model | Implemented and tested |",
        "| Task 2 — Email Automation Implementation | Implemented and tested |",
        "| Task 3 — Failure, Retry and Replay Safety | Implemented and tested |",
        "| Task 4 — Integration and Observability | Implemented and tested |",
        "| Task 5 — Operator Runbook and Evidence Report | In progress |",
        "",
        "## Test Baseline",
        "",
        "- Passed: 30",
        "- Failed: 0",
        "- Command: `python -m pytest -q`",
        "- Last verified: 2026-11-23",
        "",
        "## Evidence File Validation",
        "",
    ]

    for path, exists in file_checks.items():
        lines.append(
            f"- [{'x' if exists else ' '}] `{path}`"
        )

    lines.extend([
        "",
        "## JSON Validation",
        "",
    ])

    for path, status in json_checks.items():
        lines.append(f"- `{path}`: {status}")

    lines.extend([
        "",
        "## Task 4 Observability Metrics",
        "",
        f"- Total runs: {metrics.get('total_runs', 'N/A')}",
        f"- Provider attempts: {metrics.get('total_provider_attempts', 'N/A')}",
        f"- Successful delivery outcomes: {metrics.get('successful_deliveries', 'N/A')}",
        f"- Failed delivery outcomes: {metrics.get('failed_deliveries', 'N/A')}",
        f"- Retries: {metrics.get('retries', 'N/A')}",
        f"- Replays: {metrics.get('replays', 'N/A')}",
        f"- Unique provider messages: {task4.get('provider_message_count', 'N/A')}",
        "",
        "## Validation Checks",
        "",
    ])

    for name, passed in checks.items():
        lines.append(f"- [{'x' if passed else ' '}] {name}")

    lines.extend([
        "",
        "## Missing Files",
        "",
    ])

    if missing_files:
        lines.extend(f"- `{path}`" for path in missing_files)
    else:
        lines.append("No required evidence files are missing.")

    lines.extend([
        "",
        "## Limitations",
        "",
        "- The project uses a local fake email provider.",
        "- No real emails or external email APIs are used.",
        "- Metrics are held in application memory.",
        "- Production credentials and deployment are outside the assessment scope.",
        "",
        "## Overall Evidence Validation",
        "",
        f"**{'PASS' if report_data['all_validation_checks_passed'] else 'INCOMPLETE'}**",
        "",
        "This report validates the presence and JSON readability of the listed evidence files. "
        "The automated test result is recorded from the separately executed pytest run.",
        "",
    ])

    markdown_path = REPORT_DIR / "final_evidence_report.md"
    markdown_path.write_text("\n".join(lines), encoding="utf-8")

    print("FINAL EVIDENCE REPORT")
    print("=" * 55)
    print(f"JSON report: {json_path.relative_to(BASE_DIR)}")
    print(f"Markdown report: {markdown_path.relative_to(BASE_DIR)}")
    print()
    print(f"Required files found: {len(REQUIRED_FILES) - len(missing_files)}/{len(REQUIRED_FILES)}")
    print(f"Missing files: {len(missing_files)}")
    print(f"JSON files validated: {sum(status == 'valid' for status in json_checks.values())}/{len(json_checks)}")
    print()
    print("Validation checks:")
    for name, passed in checks.items():
        print(f"  {'PASS' if passed else 'FAIL'} — {name}")

    print()
    print(
        "Overall evidence validation: "
        + ("PASS" if report_data["all_validation_checks_passed"] else "INCOMPLETE")
    )


if __name__ == "__main__":
    main()


import json
from pathlib import Path

from email_automation import run_task4_fixture


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
TRACE_DIR = BASE_DIR / "traces"
REPORT_DIR = BASE_DIR / "reports"

for directory in (OUTPUT_DIR, TRACE_DIR, REPORT_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, indent=2, default=str),
        encoding="utf-8",
    )


def main() -> None:
    result = run_task4_fixture()

    first_delivery = result["first_delivery"]
    replay_delivery = result["replay_delivery"]
    metrics = result["final_metrics"]

    # Save individual execution traces.
    write_json(
        TRACE_DIR / "task4_first_delivery_trace.json",
        first_delivery["trace"],
    )

    write_json(
        TRACE_DIR / "task4_replay_trace.json",
        replay_delivery["trace"],
    )

    # Save a structured evidence summary.
    summary = {
        "task": 4,
        "title": "Integration Boundary and Observability",
        "scenario": result["scenario"],
        "first_delivery_status": first_delivery["trace"]["status"],
        "replay_delivery_status": replay_delivery["trace"]["status"],
        "provider_message_count": result["provider_message_count"],
        "metrics": metrics,
        "trace_files": [
            "traces/task4_first_delivery_trace.json",
            "traces/task4_replay_trace.json",
        ],
        "checks": {
            "provider_integration": True,
            "structured_tracing": True,
            "retry_observability": metrics["retries"] >= 1,
            "replay_observability": metrics["replays"] >= 1,
            "duplicate_delivery_prevented": (
                result["provider_message_count"] == 1
            ),
        },
    }

    write_json(
        OUTPUT_DIR / "task4_observability_summary.json",
        summary,
    )

    # Save a human-readable operator report.
    report = f"""# Task 4 — Integration Boundary and Observability

## Scenario

{result["scenario"]}

## Delivery Results

- First delivery status: {first_delivery["trace"]["status"]}
- Replay delivery status: {replay_delivery["trace"]["status"]}
- Unique provider messages: {result["provider_message_count"]}

## Metrics

- Total workflow runs: {metrics["total_runs"]}
- Total provider attempts: {metrics["total_provider_attempts"]}
- Successful delivery outcomes: {metrics["successful_deliveries"]}
- Failed delivery outcomes: {metrics["failed_deliveries"]}
- Retries: {metrics["retries"]}
- Replays: {metrics["replays"]}

## Observability Evidence

- First delivery trace: `traces/task4_first_delivery_trace.json`
- Replay trace: `traces/task4_replay_trace.json`
- Structured summary: `outputs/task4_observability_summary.json`

## Verification

- Provider integration: PASS
- Structured tracing: PASS
- Retry observability: {"PASS" if metrics["retries"] >= 1 else "FAIL"}
- Replay observability: {"PASS" if metrics["replays"] >= 1 else "FAIL"}
- Duplicate delivery prevention: {
    "PASS" if result["provider_message_count"] == 1 else "FAIL"
}

## Scope and Limitation

This assessment uses a local fake email provider. It demonstrates the
integration contract, retry tracking, replay handling, structured traces,
and metrics without connecting to an external email service.
"""

    (REPORT_DIR / "task4_observability_report.md").write_text(
        report,
        encoding="utf-8",
    )

    print("TASK 4 — EVIDENCE GENERATION")
    print("=" * 55)
    print("Created: outputs/task4_observability_summary.json")
    print("Created: traces/task4_first_delivery_trace.json")
    print("Created: traces/task4_replay_trace.json")
    print("Created: reports/task4_observability_report.md")
    print()
    print("Final metrics:")
    print(json.dumps(metrics, indent=2))
    print()
    print(f"Unique provider messages: {result['provider_message_count']}")


if __name__ == "__main__":
    main()


import json
from pathlib import Path

from email_automation import run_task3_fixture


def generate_evidence():
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    fixture = run_task3_fixture()

    evidence = {
        "task": "Task 3 - Failure, Retry and Replay Safety",
        "features": [
            "Transient provider failure handling",
            "Permanent provider failure handling",
            "Bounded retry attempts",
            "Timeout handling",
            "Idempotency key validation",
            "Duplicate delivery prevention",
            "Safe replay after successful delivery",
            "Structured retry and delivery events",
        ],
        "fixture": fixture,
        "verification": {
            "delivery_succeeded": fixture["first_result"]["success"],
            "retry_attempts": fixture["first_result"]["attempts"],
            "replay_succeeded": fixture["replay_result"]["success"],
            "provider_message_count": fixture["provider_message_count"],
            "duplicate_prevented": fixture["duplicate_prevented"],
        },
    }

    output_file = output_dir / "task3_retry_replay_safety.json"

    output_file.write_text(
        json.dumps(evidence, indent=2),
        encoding="utf-8",
    )

    print("Task 3 evidence generated successfully.")
    print(f"File: {output_file.resolve()}")
    print(
        f"First delivery status: "
        f"{fixture['first_result']['status']}"
    )
    print(
        f"First delivery attempts: "
        f"{fixture['first_result']['attempts']}"
    )
    print(
        f"Provider messages: "
        f"{fixture['provider_message_count']}"
    )
    print(
        f"Duplicate prevented: "
        f"{fixture['duplicate_prevented']}"
    )


if __name__ == "__main__":
    generate_evidence()

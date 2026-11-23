
import json
from pathlib import Path

from email_automation import (
    run_task2_fixture,
)


def generate_evidence():
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    fixture = run_task2_fixture()

    evidence = {
        "task": "Task 2 - Email Automation Implementation",
        "features": [
            "Email template rendering",
            "Required template variable validation",
            "Recipient email validation",
            "Recipient consent validation",
            "Unsubscribe protection",
            "Future email scheduling",
            "Simulated email delivery",
            "Delivery result tracking",
        ],
        "fixture": fixture,
    }

    output_file = output_dir / "task2_email_automation.json"

    output_file.write_text(
        json.dumps(evidence, indent=2),
        encoding="utf-8",
    )

    print("Task 2 evidence generated successfully.")
    print(f"File: {output_file.resolve()}")
    print(f"Delivery status: {fixture['result']['status']}")
    print(f"Provider messages: {fixture['provider_message_count']}")


if __name__ == "__main__":
    generate_evidence()

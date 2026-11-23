
import json
from pathlib import Path

from email_automation import (
    LEGAL_TRANSITIONS,
    run_task1_fixture,
)


def generate_evidence():
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    fixture = run_task1_fixture()

    evidence = {
        "task": "Task 1 - Workflow Contract and State Model",
        "workflow_states": [
            state.value for state in __import__(
                "email_automation"
            ).WorkflowState
        ],
        "legal_transitions": {
            state.value: {
                event: next_state.value
                for event, next_state in transitions.items()
            }
            for state, transitions in LEGAL_TRANSITIONS.items()
        },
        "fixture": fixture,
    }

    output_file = output_dir / "task1_workflow_contract.json"

    output_file.write_text(
        json.dumps(evidence, indent=2),
        encoding="utf-8",
    )

    print("Task 1 evidence generated successfully.")
    print(f"File: {output_file.resolve()}")
    print(f"Final workflow state: {fixture['state']}")
    print(f"Events recorded: {len(fixture['events'])}")
    print(f"Tasks created: {len(fixture['tasks'])}")


if __name__ == "__main__":
    generate_evidence()

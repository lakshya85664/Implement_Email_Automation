
# Operator Runbook — Email Automation

## 1. Project Overview

This project implements a local email automation workflow for invoice reminders. It demonstrates workflow state management, email validation, recipient consent, scheduling, delivery, bounded retries, replay safety, provider integration, and observability.

The implementation uses a fake email provider. No real emails are sent.

## 2. Environment Requirements

- Python 3.13.9
- Pydantic 2.14.3
- Pytest 9.2.0
- Windows command prompt
- Virtual environment (`.venv`)

## 3. Activate the Environment

Open Command Prompt and navigate to the project directory:

```cmd
cd /d E:\Tayana_Projects\Workflow_Orchestration\Implement_Email_Automation
```

Activate the virtual environment:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```cmd
pip install -r requirements.txt
```

## 4. Execute the Workflow

Run the main implementation:

```cmd
python email_automation.py
```

The program demonstrates the workflow fixtures, including email automation, retry handling, replay safety, and observability.

## 5. Generate Evidence

Generate evidence for the individual assessment tasks:

```cmd
python generate_task1_evidence.py
python generate_task2_evidence.py
python generate_task3_evidence.py
python generate_task4_evidence.py
```

Evidence is saved in the following directories:

- `outputs/` — structured task evidence in JSON format.
- `traces/` — execution trace records.
- `reports/` — human-readable reports.
- `diagrams/` — workflow state diagram.

## 6. Run Automated Tests

Run the complete test suite:

```cmd
python -m pytest -q
```

The verified baseline after Task 4 is 30 passing tests.

## 7. Workflow Operations

### Validation

Validate the recipient email address, template, and recipient consent before delivery.

### Scheduling

Future-dated reminders are scheduled rather than sent immediately.

### Delivery

The email gateway provides a provider-independent integration boundary. The local fake provider simulates delivery.

### Retry Handling

Transient provider failures and timeouts can be retried within the configured attempt limit. Permanent failures are not retried.

### Replay Safety

An idempotency key identifies the logical delivery operation. Repeated requests with the same key reuse the existing provider result and prevent duplicate messages.

### Observability

Structured traces record delivery events, attempts, failures, retries, replay events, and completion status. Metrics track runs, provider attempts, successes, failures, retries, and replays.

## 8. Troubleshooting

| Problem | Recommended action |
|---|---|
| Module not found | Activate `.venv` and install `requirements.txt` |
| Validation failure | Check recipient, template, and consent inputs |
| Permanent provider error | Inspect the error; do not retry automatically |
| Transient provider error | Check retry events and configured attempt limit |
| Duplicate delivery concern | Verify the idempotency key and provider message count |
| Missing evidence | Run the corresponding evidence generator |
| Test failure | Inspect the failing assertion and traceback |

## 9. Evidence Locations

| Assessment task | Evidence |
|---|---|
| Task 1 — Workflow contract | `outputs/task1_workflow_contract.json` |
| Task 2 — Email automation | `outputs/task2_email_automation.json` |
| Task 3 — Retry and replay safety | `outputs/task3_retry_replay_safety.json` |
| Task 4 — Observability | `outputs/task4_observability_summary.json` |
| Task 4 — First delivery trace | `traces/task4_first_delivery_trace.json` |
| Task 4 — Replay trace | `traces/task4_replay_trace.json` |
| Task 4 — Observability report | `reports/task4_observability_report.md` |
| State diagram | `diagrams/state_transitions.md` |

## 10. Security and Operational Limitations

- The implementation uses a fake local provider.
- No production email service or external API is connected.
- Credentials and production secrets are not required.
- The fake provider does not demonstrate real-world deliverability.
- Production deployment would require secure credential management, provider-specific error handling, monitoring, and operational access controls.
- The current metrics are maintained in application memory and are not persistent across separate process executions.

## 11. Operator Checklist

Before completing an assessment run:

1. Activate the virtual environment.
2. Confirm dependencies are installed.
3. Execute the workflow.
4. Generate the required evidence files.
5. Run the automated tests.
6. Inspect the generated outputs, traces, and reports.
7. Confirm that no real external email service was used.

## 12. Assessment Completion Status

Tasks 1–4 have been implemented and verified with 30 passing automated tests.

Task 5 documentation and final evidence validation complete the assessment package.

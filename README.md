# Topic 17 — Email Automation

## Project Overview

This project implements a local email automation workflow for invoice reminders. It demonstrates how an automated email system can validate incoming requests, manage workflow states, schedule messages, handle delivery failures, prevent duplicate sends, and record execution details.

The implementation is developed in Python using Pydantic for data validation and Pytest for automated testing. A fake email provider is used to simulate delivery without sending real emails or connecting to an external email service.

## Learning Objectives

- Design typed workflow inputs and execution models.
- Define workflow states and legal state transitions.
- Validate email addresses, templates, and recipient consent.
- Implement email scheduling and delivery.
- Handle transient and permanent provider failures.
- Apply bounded retries and idempotency-based replay safety.
- Establish a provider-independent integration boundary.
- Generate structured traces and delivery metrics.
- Prepare operational documentation and assessment evidence.

## Project Structure

```text
Implement_Email_Automation/
│
├── email_automation.py
├── generate_task1_evidence.py
├── generate_task2_evidence.py
├── generate_task3_evidence.py
├── generate_task4_evidence.py
├── generate_final_evidence.py
├── requirements.txt
├── README.md
├── OPERATOR_RUNBOOK.md
├── .gitignore
│
├── diagrams/
│   └── state_transitions.md
│
├── tests/
│   └── test_email_automation.py
│
├── outputs/
│   ├── task1_workflow_contract.json
│   ├── task2_email_automation.json
│   ├── task3_retry_replay_safety.json
│   ├── task4_observability_summary.json
│   └── final_evidence_report.json
│
├── traces/
│   ├── task4_first_delivery_trace.json
│   └── task4_replay_trace.json
│
└── reports/
    ├── task4_observability_report.md
    └── final_evidence_report.md
```

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.13.9 | Core implementation |
| Pydantic 2.14.3 | Data validation and structured models |
| Pytest 9.2.0 | Automated testing |
| JSON | Structured evidence and trace storage |
| Markdown | Documentation and operator runbook |

## Assessment Tasks

### Task 1 — Workflow Contract and State Model

Designed the workflow contract using typed models for email input, workflow runs, tasks, events, traces, and results.

Defined workflow states and legal transitions to ensure that workflow execution follows controlled state changes.

**Evidence:** `outputs/task1_workflow_contract.json`

### Task 2 — Email Automation Implementation

Implemented email template validation, recipient email validation, consent verification, scheduling, and delivery using a local fake email provider.

The implementation supports future-dated reminders without sending them prematurely.

**Evidence:** `outputs/task2_email_automation.json`

### Task 3 — Failure, Retry and Replay Safety

Implemented transient and permanent provider error handling, bounded retries, timeout handling, and idempotency-based replay protection.

The demonstration simulates a transient failure followed by successful delivery. Replaying the same request reuses the existing provider result instead of creating another message.

**Evidence:** `outputs/task3_retry_replay_safety.json`

### Task 4 — Integration Boundary and Observability

Introduced a provider-independent email gateway contract and a fake gateway adapter.

Added structured execution traces and metrics for workflow runs, provider attempts, successful and failed outcomes, retries, and replays.

Verified that replaying a delivery does not create a duplicate provider message.

**Evidence:**
- `outputs/task4_observability_summary.json`
- `traces/task4_first_delivery_trace.json`
- `traces/task4_replay_trace.json`
- `reports/task4_observability_report.md`

### Task 5 — Operator Runbook and Evidence Report

Prepared an operator runbook containing environment setup, execution commands, evidence-generation instructions, troubleshooting guidance, and operational limitations.

Generated a consolidated evidence report to validate required files and JSON evidence.

**Evidence:**
- `OPERATOR_RUNBOOK.md`
- `outputs/final_evidence_report.json`
- `reports/final_evidence_report.md`

## Installation and Setup

### 1. Clone the repository

```cmd
git clone <your-github-repository-url>
cd Implement_Email_Automation
```

### 2. Create a virtual environment

```cmd
python -m venv .venv
```

### 3. Activate the environment

```cmd
.venv\Scripts\activate
```

### 4. Install dependencies

```cmd
pip install -r requirements.txt
```

## Running the Project

Execute the main implementation:

```cmd
python email_automation.py
```

Generate task evidence:

```cmd
python generate_task1_evidence.py
python generate_task2_evidence.py
python generate_task3_evidence.py
python generate_task4_evidence.py
```

Generate the consolidated evidence report:

```cmd
python generate_final_evidence.py
```

## Running Automated Tests

Execute the complete test suite:

```cmd
python -m pytest -q
```

**Verified result:** 30 passed.

The test suite covers workflow transitions, input validation, email automation, scheduling, failure handling, retries, replay safety, gateway integration, structured tracing, and metrics.

## Task 4 Observability Results

The local demonstration produced the following metrics:

| Metric | Result |
|---|---:|
| Total workflow runs | 2 |
| Provider attempts | 3 |
| Successful delivery outcomes | 2 |
| Failed delivery outcomes | 0 |
| Retries | 1 |
| Replays | 1 |
| Unique provider messages | 1 |

These results demonstrate successful retry handling and duplicate prevention through idempotency.

## Security and Limitations

- The project uses a local fake email provider.
- No real emails are sent.
- No external email provider or production API is connected.
- Metrics are maintained in application memory.
- Production deployment would require secure credential management, provider-specific integration, persistent monitoring, and additional operational controls.

## Reflection

This project helped me understand how an email automation workflow can be designed as a structured and reliable system rather than a simple script that sends messages. I learned how workflow states, typed data models, validation rules, and legal transitions help maintain control over an automation process.

During the implementation, I worked on validating email addresses, checking recipient consent, validating templates, and handling scheduled delivery. I also learned why failure handling is important in real-world automation. A provider request can fail temporarily, time out, or fail permanently, so the system needs a controlled retry strategy instead of repeatedly attempting every failed operation.

One of the most important concepts I implemented was idempotency. Replaying an email request should not result in multiple messages being sent to the same recipient. Using an idempotency key helped demonstrate how duplicate delivery can be prevented even when a workflow is executed again.

I also gained practical experience with provider abstraction and observability. By introducing a gateway interface, the workflow can communicate with a provider without depending directly on its implementation. Structured traces and metrics made it easier to understand execution attempts, retries, replay events, and final delivery outcomes.

Testing each task independently helped me identify implementation issues early and verify the behavior before moving forward. The final test suite passed all 30 tests.

Overall, this assessment improved my understanding of workflow orchestration, failure recovery, replay safety, integration boundaries, and operational documentation. It also showed me why reliability, traceability, and maintainability are essential when building production-oriented automation systems.

## Conclusion

The Email Automation assessment demonstrates a complete local workflow covering state management, validation, scheduling, delivery simulation, retry handling, replay protection, provider abstraction, observability, and operational documentation.

All five assessment tasks have been implemented, and the final verified automated test suite contains 30 passing tests.
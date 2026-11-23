
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# 1. WORKFLOW STATES
# ============================================================

class WorkflowState(str, Enum):
    CREATED = "created"
    VALIDATED = "validated"
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    RUNNING = "running"
    SENT = "sent"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    CANCELLED = "cancelled"


# ============================================================
# 2. TASK STATES
# ============================================================

class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ============================================================
# 3. INPUT MODEL
# ============================================================

class EmailInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    recipient: str
    subject: str
    template_id: str
    invoice_id: str
    amount: float = Field(gt=0)
    currency: str = "INR"
    scheduled_at: datetime | None = None


# ============================================================
# 4. TASK MODEL
# ============================================================

class WorkflowTask(BaseModel):
    task_id: str
    name: str
    owner: str = "email_automation"
    state: TaskState = TaskState.PENDING
    attempts: int = 0
    depends_on: list[str] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# 5. EVENT AND TRACE MODELS
# ============================================================

class WorkflowEvent(BaseModel):
    event_id: str
    run_id: str
    event: str
    state: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    details: dict[str, Any] = Field(default_factory=dict)


class WorkflowTrace(BaseModel):
    run_id: str
    business_key: str
    events: list[WorkflowEvent] = Field(default_factory=list)


# ============================================================
# 6. RESULT MODEL
# ============================================================

class WorkflowResult(BaseModel):
    run_id: str
    state: WorkflowState
    success: bool
    message: str
    next_action: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# 7. WORKFLOW RUN MODEL
# ============================================================

class WorkflowRun(BaseModel):
    run_id: str
    business_key: str
    state: WorkflowState = WorkflowState.CREATED
    attempts: int = 0
    context: dict[str, Any] = Field(default_factory=dict)
    tasks: list[WorkflowTask] = Field(default_factory=list)
    events: list[WorkflowEvent] = Field(default_factory=list)

    def record(self, event: str, **details: Any) -> None:
        """Record a structured workflow event."""
        self.events.append(
            WorkflowEvent(
                event_id=f"EVT-{len(self.events) + 1:04d}",
                run_id=self.run_id,
                event=event,
                state=self.state.value,
                details=details,
            )
        )


# ============================================================
# 8. LEGAL STATE TRANSITIONS
# ============================================================

LEGAL_TRANSITIONS = {
    WorkflowState.CREATED: {
        "validate": WorkflowState.VALIDATED,
        "cancel": WorkflowState.CANCELLED,
    },
    WorkflowState.VALIDATED: {
        "schedule": WorkflowState.SCHEDULED,
        "queue": WorkflowState.QUEUED,
        "block": WorkflowState.NEEDS_REVIEW,
        "cancel": WorkflowState.CANCELLED,
    },
    WorkflowState.SCHEDULED: {
        "queue": WorkflowState.QUEUED,
        "cancel": WorkflowState.CANCELLED,
    },
    WorkflowState.QUEUED: {
        "start": WorkflowState.RUNNING,
        "cancel": WorkflowState.CANCELLED,
    },
    WorkflowState.RUNNING: {
        "complete": WorkflowState.SENT,
        "fail": WorkflowState.FAILED,
        "review": WorkflowState.NEEDS_REVIEW,
    },
    WorkflowState.FAILED: {
        "retry": WorkflowState.QUEUED,
        "review": WorkflowState.NEEDS_REVIEW,
    },
    WorkflowState.NEEDS_REVIEW: {
        "retry": WorkflowState.QUEUED,
        "cancel": WorkflowState.CANCELLED,
    },
    WorkflowState.SENT: {},
    WorkflowState.CANCELLED: {},
}


# ============================================================
# 9. TRANSITION FUNCTION
# ============================================================

def transition(run: WorkflowRun, event: str) -> WorkflowRun:
    """Apply a legal workflow state transition."""

    next_state = LEGAL_TRANSITIONS.get(run.state, {}).get(event)

    if next_state is None:
        raise ValueError(
            f"Illegal transition: {run.state.value} + {event}"
        )

    previous_state = run.state
    run.state = next_state

    run.record(
        event=event,
        previous_state=previous_state.value,
        next_state=next_state.value,
    )

    return run


# ============================================================
# 10. TASK 1 FIXTURE
# ============================================================

def run_task1_fixture() -> dict[str, Any]:
    """Run a deterministic Task 1 workflow demonstration."""

    run = WorkflowRun(
        run_id="EMAIL-RUN-001",
        business_key="INVOICE-1001",
        context={
            "topic": "Email Automation",
            "recipient": "customer@example.com",
            "invoice_id": "INV-1001",
        },
    )

    run.tasks.append(
        WorkflowTask(
            task_id="TASK-001",
            name="Validate recipient and consent",
            owner="validation_service",
        )
    )

    run.tasks.append(
        WorkflowTask(
            task_id="TASK-002",
            name="Prepare invoice reminder",
            owner="email_service",
            depends_on=["TASK-001"],
        )
    )

    transition(run, "validate")
    transition(run, "queue")

    return {
        "run_id": run.run_id,
        "business_key": run.business_key,
        "state": run.state.value,
        "tasks": [
            task.model_dump(mode="json")
            for task in run.tasks
        ],
        "events": [
            event.model_dump(mode="json")
            for event in run.events
        ],
    }


if __name__ == "__main__":
    import json

    result = run_task1_fixture()
    print(json.dumps(result, indent=2, default=str))


# ============================================================
# TASK 2 — EMAIL AUTOMATION IMPLEMENTATION
# ============================================================

import re
from enum import Enum
from typing import Protocol


# ------------------------------------------------------------
# 1. EMAIL TEMPLATE MODEL
# ------------------------------------------------------------

class EmailTemplate(BaseModel):
    template_id: str
    subject_template: str
    body_template: str
    required_variables: list[str] = Field(default_factory=list)


# ------------------------------------------------------------
# 2. RECIPIENT CONSENT MODEL
# ------------------------------------------------------------

class RecipientConsent(BaseModel):
    email: str
    consent_granted: bool
    unsubscribed: bool = False


# ------------------------------------------------------------
# 3. DELIVERY STATUS
# ------------------------------------------------------------

class DeliveryStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    REJECTED = "rejected"


# ------------------------------------------------------------
# 4. EMAIL DELIVERY RESULT
# ------------------------------------------------------------

class EmailDeliveryResult(BaseModel):
    run_id: str
    recipient: str
    status: DeliveryStatus
    provider_message_id: str | None = None
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    subject: str | None = None
    reason: str | None = None


# ------------------------------------------------------------
# 5. FAKE EMAIL PROVIDER
# ------------------------------------------------------------

class EmailProvider(Protocol):
    def send(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> str:
        ...


class FakeEmailProvider:
    """Local email provider for deterministic testing."""

    def __init__(self):
        self.sent_messages: list[dict[str, Any]] = []

    def send(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> str:

        message_id = f"FAKE-MSG-{len(self.sent_messages) + 1:04d}"

        self.sent_messages.append({
            "message_id": message_id,
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "status": "sent",
        })

        return message_id


# ------------------------------------------------------------
# 6. EMAIL VALIDATION
# ------------------------------------------------------------

def validate_email_address(email: str) -> bool:
    """Perform basic email address validation."""

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return re.fullmatch(pattern, email) is not None


def validate_template(
    template: EmailTemplate,
    variables: dict[str, Any],
) -> tuple[str, str]:
    """Validate required template variables and render content."""

    missing = [
        name
        for name in template.required_variables
        if name not in variables
    ]

    if missing:
        raise ValueError(
            f"Missing template variables: {', '.join(missing)}"
        )

    try:
        subject = template.subject_template.format(**variables)
        body = template.body_template.format(**variables)
    except (KeyError, ValueError, IndexError) as exc:
        raise ValueError(
            f"Template rendering failed: {exc}"
        ) from exc

    if not subject.strip() or not body.strip():
        raise ValueError("Rendered subject and body cannot be empty")

    return subject, body


# ------------------------------------------------------------
# 7. RECIPIENT CONSENT VALIDATION
# ------------------------------------------------------------

def validate_recipient_consent(
    recipient: str,
    consent: RecipientConsent,
) -> None:
    """Reject invalid, unconsented, or unsubscribed recipients."""

    if not validate_email_address(recipient):
        raise ValueError("Invalid recipient email address")

    if recipient.lower() != consent.email.lower():
        raise ValueError("Consent record does not match recipient")

    if not consent.consent_granted:
        raise PermissionError("Recipient has not granted email consent")

    if consent.unsubscribed:
        raise PermissionError("Recipient has unsubscribed")


# ------------------------------------------------------------
# 8. MAIN EMAIL AUTOMATION FUNCTION
# ------------------------------------------------------------

def send_invoice_reminder(
    email_input: EmailInput,
    template: EmailTemplate,
    consent: RecipientConsent,
    provider: EmailProvider,
    run_id: str,
) -> EmailDeliveryResult:
    """
    Validate, schedule, and send an invoice reminder.

    External delivery happens only after all validation checks.
    """

    validate_recipient_consent(
        email_input.recipient,
        consent,
    )

    variables = {
        "recipient": email_input.recipient,
        "invoice_id": email_input.invoice_id,
        "amount": f"{email_input.amount:.2f}",
        "currency": email_input.currency,
    }

    subject, body = validate_template(
        template,
        variables,
    )

    now = datetime.now(timezone.utc)

    if email_input.scheduled_at is not None:
        scheduled_at = email_input.scheduled_at

        if scheduled_at.tzinfo is None:
            raise ValueError(
                "scheduled_at must include timezone information"
            )

        if scheduled_at > now:
            return EmailDeliveryResult(
                run_id=run_id,
                recipient=email_input.recipient,
                status=DeliveryStatus.SCHEDULED,
                scheduled_at=scheduled_at,
                subject=subject,
                reason="Email is waiting for its scheduled time",
            )

    message_id = provider.send(
        recipient=email_input.recipient,
        subject=subject,
        body=body,
    )

    return EmailDeliveryResult(
        run_id=run_id,
        recipient=email_input.recipient,
        status=DeliveryStatus.SENT,
        provider_message_id=message_id,
        scheduled_at=email_input.scheduled_at,
        sent_at=datetime.now(timezone.utc),
        subject=subject,
        reason="Email accepted by simulated provider",
    )


# ------------------------------------------------------------
# 9. TASK 2 DETERMINISTIC FIXTURE
# ------------------------------------------------------------

def run_task2_fixture() -> dict[str, Any]:
    """Demonstrate successful invoice reminder delivery."""

    email_input = EmailInput(
        recipient="customer@example.com",
        subject="Invoice Reminder",
        template_id="invoice_reminder_v1",
        invoice_id="INV-2001",
        amount=4500.00,
        currency="INR",
    )

    template = EmailTemplate(
        template_id="invoice_reminder_v1",
        subject_template="Reminder: Invoice {invoice_id}",
        body_template=(
            "Hello {recipient},\n\n"
            "This is a reminder for invoice {invoice_id}.\n"
            "Outstanding amount: {currency} {amount}.\n\n"
            "Please review and complete your payment.\n"
            "Thank you."
        ),
        required_variables=[
            "recipient",
            "invoice_id",
            "amount",
            "currency",
        ],
    )

    consent = RecipientConsent(
        email="customer@example.com",
        consent_granted=True,
        unsubscribed=False,
    )

    provider = FakeEmailProvider()

    result = send_invoice_reminder(
        email_input=email_input,
        template=template,
        consent=consent,
        provider=provider,
        run_id="EMAIL-RUN-TASK2-001",
    )

    return {
        "scenario": "successful_invoice_reminder",
        "result": result.model_dump(mode="json"),
        "provider_message_count": len(provider.sent_messages),
        "provider_messages": provider.sent_messages,
    }


# ------------------------------------------------------------
# 10. TASK 2 EXECUTION ENTRY POINT
# ------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("\nTASK 2 — EMAIL AUTOMATION")
    print("=" * 60)

    task2_result = run_task2_fixture()

    print(json.dumps(task2_result, indent=2, default=str))


# ============================================================
# TASK 3 — FAILURE, RETRY AND REPLAY SAFETY
# ============================================================

class TransientProviderError(Exception):
    """A temporary provider failure that may succeed on retry."""


class PermanentProviderError(Exception):
    """A permanent provider failure that should not be retried."""


class Task3FakeEmailProvider:
    """
    Local provider that simulates failures and supports idempotency.

    The same idempotency key can create at most one sent message.
    """

    def __init__(self, outcomes: list[str] | None = None):
        self.outcomes = list(outcomes or [])
        self.sent_messages: list[dict[str, Any]] = []
        self.idempotency_records: dict[str, dict[str, Any]] = {}
        self.call_count = 0

    def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        idempotency_key: str,
    ) -> dict[str, Any]:

        if idempotency_key in self.idempotency_records:
            return {
                **self.idempotency_records[idempotency_key],
                "replayed": True,
            }

        self.call_count += 1

        outcome = (
            self.outcomes.pop(0)
            if self.outcomes
            else "success"
        )

        if outcome == "transient":
            raise TransientProviderError(
                "Simulated temporary provider failure"
            )

        if outcome == "permanent":
            raise PermanentProviderError(
                "Simulated permanent provider rejection"
            )

        if outcome == "timeout":
            raise TimeoutError(
                "Simulated provider timeout"
            )

        if outcome != "success":
            raise ValueError(f"Unknown provider outcome: {outcome}")

        message = {
            "message_id": f"TASK3-MSG-{len(self.sent_messages) + 1:04d}",
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "status": "sent",
            "idempotency_key": idempotency_key,
        }

        self.sent_messages.append(message)
        self.idempotency_records[idempotency_key] = message

        return {
            **message,
            "replayed": False,
        }


def send_with_retry(
    provider: Task3FakeEmailProvider,
    recipient: str,
    subject: str,
    body: str,
    idempotency_key: str,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """
    Send an email with bounded retries and structured attempt events.

    Retries transient errors and timeouts only.
    Permanent failures are returned immediately.
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    if not idempotency_key.strip():
        raise ValueError("idempotency_key cannot be empty")

    events: list[dict[str, Any]] = []

    for attempt in range(1, max_attempts + 1):
        try:
            result = provider.send(
                recipient=recipient,
                subject=subject,
                body=body,
                idempotency_key=idempotency_key,
            )

            event_type = (
                "replay_success"
                if result.get("replayed")
                else "delivery_success"
            )

            events.append({
                "event": event_type,
                "attempt": attempt,
                "message_id": result["message_id"],
            })

            return {
                "status": "sent",
                "success": True,
                "attempts": attempt,
                "max_attempts": max_attempts,
                "message": result,
                "events": events,
                "error": None,
            }

        except PermanentProviderError as exc:
            events.append({
                "event": "permanent_failure",
                "attempt": attempt,
                "error": str(exc),
            })

            return {
                "status": "failed",
                "success": False,
                "attempts": attempt,
                "max_attempts": max_attempts,
                "message": None,
                "events": events,
                "error": str(exc),
            }

        except (TransientProviderError, TimeoutError) as exc:
            error_type = (
                "timeout"
                if isinstance(exc, TimeoutError)
                else "transient_failure"
            )

            events.append({
                "event": error_type,
                "attempt": attempt,
                "error": str(exc),
            })

            if attempt == max_attempts:
                events.append({
                    "event": "retry_exhausted",
                    "attempt": attempt,
                })

                return {
                    "status": "failed",
                    "success": False,
                    "attempts": attempt,
                    "max_attempts": max_attempts,
                    "message": None,
                    "events": events,
                    "error": str(exc),
                }

            events.append({
                "event": "retry_scheduled",
                "attempt": attempt,
                "next_attempt": attempt + 1,
            })

    raise RuntimeError("Unexpected retry loop termination")


def run_task3_fixture() -> dict[str, Any]:
    """Demonstrate transient failure, retry, success and safe replay."""

    provider = Task3FakeEmailProvider(
        outcomes=["transient", "success"]
    )

    first_result = send_with_retry(
        provider=provider,
        recipient="customer@example.com",
        subject="Reminder: Invoice INV-3001",
        body="Your invoice payment reminder.",
        idempotency_key="invoice:INV-3001:reminder:v1",
        max_attempts=3,
    )

    replay_result = send_with_retry(
        provider=provider,
        recipient="customer@example.com",
        subject="Reminder: Invoice INV-3001",
        body="Your invoice payment reminder.",
        idempotency_key="invoice:INV-3001:reminder:v1",
        max_attempts=3,
    )

    return {
        "scenario": "transient_failure_retry_and_safe_replay",
        "first_result": first_result,
        "replay_result": replay_result,
        "provider_call_count": provider.call_count,
        "provider_message_count": len(provider.sent_messages),
        "provider_messages": provider.sent_messages,
        "duplicate_prevented": len(provider.sent_messages) == 1,
    }


if __name__ == "__main__":
    import json

    print("\nTASK 3 — FAILURE, RETRY AND REPLAY SAFETY")
    print("=" * 60)

    task3_result = run_task3_fixture()
    print(json.dumps(task3_result, indent=2, default=str))


# ============================================================
# TASK 4 — INTEGRATION BOUNDARY AND OBSERVABILITY
# ============================================================

from typing import Protocol
from uuid import uuid4


class EmailGateway(Protocol):
    """Provider-independent email integration contract."""

    def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        ...


class FakeEmailGateway:
    """
    Adapter that exposes the local Task 3 provider
    through the provider-independent gateway contract.
    """

    def __init__(self, provider: Task3FakeEmailProvider):
        self.provider = provider

    def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        idempotency_key: str,
    ) -> dict[str, Any]:

        return self.provider.send(
            recipient=recipient,
            subject=subject,
            body=body,
            idempotency_key=idempotency_key,
        )


class TraceEvent(BaseModel):
    trace_id: str
    run_id: str
    event: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    attempt: int = 0
    details: dict[str, Any] = Field(default_factory=dict)


class EmailTrace(BaseModel):
    trace_id: str
    run_id: str
    business_key: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str = "running"
    events: list[TraceEvent] = Field(default_factory=list)

    def record(
        self,
        event: str,
        attempt: int = 0,
        **details: Any,
    ) -> None:
        self.events.append(
            TraceEvent(
                trace_id=self.trace_id,
                run_id=self.run_id,
                event=event,
                attempt=attempt,
                details=details,
            )
        )


class EmailMetrics(BaseModel):
    total_runs: int = 0
    total_provider_attempts: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    retries: int = 0
    replays: int = 0


def run_observed_email_delivery(
    gateway: EmailGateway,
    recipient: str,
    subject: str,
    body: str,
    idempotency_key: str,
    run_id: str,
    business_key: str,
    max_attempts: int = 3,
    metrics: EmailMetrics | None = None,
) -> dict[str, Any]:
    """
    Execute delivery through an integration boundary.

    Produces a structured trace and updates shared metrics.
    """

    if metrics is None:
        metrics = EmailMetrics()

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    trace = EmailTrace(
        trace_id=f"TRACE-{uuid4().hex[:12].upper()}",
        run_id=run_id,
        business_key=business_key,
        started_at=datetime.now(timezone.utc),
    )

    metrics.total_runs += 1

    trace.record(
        "delivery_started",
        recipient=recipient,
        business_key=business_key,
        idempotency_key=idempotency_key,
    )

    attempts = 0
    result = None
    error_message = None

    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        metrics.total_provider_attempts += 1

        try:
            result = gateway.send(
                recipient=recipient,
                subject=subject,
                body=body,
                idempotency_key=idempotency_key,
            )

            if result.get("replayed"):
                metrics.replays += 1
                trace.record(
                    "delivery_replayed",
                    attempt=attempt,
                    message_id=result["message_id"],
                )
            else:
                trace.record(
                    "delivery_succeeded",
                    attempt=attempt,
                    message_id=result["message_id"],
                )

            metrics.successful_deliveries += 1
            trace.status = "sent"
            break

        except PermanentProviderError as exc:
            error_message = str(exc)

            trace.record(
                "permanent_failure",
                attempt=attempt,
                error=error_message,
            )
            trace.status = "failed"
            break

        except (TransientProviderError, TimeoutError) as exc:
            error_message = str(exc)

            event_name = (
                "provider_timeout"
                if isinstance(exc, TimeoutError)
                else "transient_failure"
            )

            trace.record(
                event_name,
                attempt=attempt,
                error=error_message,
            )

            if attempt < max_attempts:
                metrics.retries += 1
                trace.record(
                    "retry_scheduled",
                    attempt=attempt,
                    next_attempt=attempt + 1,
                )
            else:
                trace.record(
                    "retry_exhausted",
                    attempt=attempt,
                )
                trace.status = "failed"

    if result is None:
        metrics.failed_deliveries += 1
        trace.status = "failed"

    trace.completed_at = datetime.now(timezone.utc)

    trace.record(
        "delivery_completed",
        attempt=attempts,
        status=trace.status,
        error=error_message,
    )

    return {
        "trace": trace.model_dump(mode="json"),
        "result": result,
        "error": error_message,
        "metrics": metrics.model_dump(mode="json"),
    }


def run_task4_fixture() -> dict[str, Any]:
    """Demonstrate tracing, metrics and provider integration."""

    provider = Task3FakeEmailProvider(
        outcomes=["transient", "success"]
    )

    gateway = FakeEmailGateway(provider)
    metrics = EmailMetrics()

    first_result = run_observed_email_delivery(
        gateway=gateway,
        recipient="customer@example.com",
        subject="Reminder: Invoice INV-4001",
        body="Your invoice payment reminder.",
        idempotency_key="invoice:INV-4001:reminder:v1",
        run_id="EMAIL-RUN-TASK4-001",
        business_key="INV-4001",
        max_attempts=3,
        metrics=metrics,
    )

    replay_result = run_observed_email_delivery(
        gateway=gateway,
        recipient="customer@example.com",
        subject="Reminder: Invoice INV-4001",
        body="Your invoice payment reminder.",
        idempotency_key="invoice:INV-4001:reminder:v1",
        run_id="EMAIL-RUN-TASK4-002",
        business_key="INV-4001",
        max_attempts=3,
        metrics=metrics,
    )

    return {
        "scenario": "provider_integration_with_observability",
        "first_delivery": first_result,
        "replay_delivery": replay_result,
        "final_metrics": metrics.model_dump(mode="json"),
        "provider_message_count": len(provider.sent_messages),
        "provider_messages": provider.sent_messages,
    }


if __name__ == "__main__":
    import json

    print("\nTASK 4 — INTEGRATION AND OBSERVABILITY")
    print("=" * 60)

    task4_result = run_task4_fixture()
    print(json.dumps(task4_result, indent=2, default=str))


import pytest

from email_automation import (
    EmailInput,
    WorkflowRun,
    WorkflowState,
    WorkflowTask,
    TaskState,
    transition,
    run_task1_fixture,
)


def create_run():
    return WorkflowRun(
        run_id="TEST-RUN-001",
        business_key="INVOICE-TEST-001",
    )


def test_legal_transition_created_to_validated():
    run = create_run()

    transition(run, "validate")

    assert run.state == WorkflowState.VALIDATED
    assert len(run.events) == 1


def test_legal_transition_validated_to_queued():
    run = create_run()

    transition(run, "validate")
    transition(run, "queue")

    assert run.state == WorkflowState.QUEUED
    assert len(run.events) == 2


def test_illegal_transition_created_to_sent():
    run = create_run()

    with pytest.raises(ValueError, match="Illegal transition"):
        transition(run, "complete")

    assert run.state == WorkflowState.CREATED
    assert len(run.events) == 0


def test_illegal_transition_sent_to_queued():
    run = create_run()

    transition(run, "validate")
    transition(run, "queue")
    transition(run, "start")
    transition(run, "complete")

    with pytest.raises(ValueError, match="Illegal transition"):
        transition(run, "retry")

    assert run.state == WorkflowState.SENT


def test_workflow_task_defaults():
    task = WorkflowTask(
        task_id="TASK-001",
        name="Validate recipient",
    )

    assert task.state == TaskState.PENDING
    assert task.attempts == 0
    assert task.depends_on == []


def test_email_input_validation():
    email = EmailInput(
        recipient="customer@example.com",
        subject="Invoice Reminder",
        template_id="invoice_reminder_v1",
        invoice_id="INV-1001",
        amount=4500,
    )

    assert email.amount == 4500
    assert email.currency == "INR"


def test_email_input_rejects_invalid_amount():
    with pytest.raises(ValueError):
        EmailInput(
            recipient="customer@example.com",
            subject="Invoice Reminder",
            template_id="invoice_reminder_v1",
            invoice_id="INV-1001",
            amount=-100,
        )


def test_task1_fixture():
    result = run_task1_fixture()

    assert result["run_id"] == "EMAIL-RUN-001"
    assert result["state"] == "queued"
    assert len(result["tasks"]) == 2
    assert len(result["events"]) == 2


# ============================================================
# TASK 2 TESTS — EMAIL AUTOMATION
# ============================================================

from datetime import datetime, timedelta, timezone

from email_automation import (
    EmailTemplate,
    RecipientConsent,
    FakeEmailProvider,
    DeliveryStatus,
    send_invoice_reminder,
    run_task2_fixture,
)


def create_task2_data():
    email_input = EmailInput(
        recipient="customer@example.com",
        subject="Invoice Reminder",
        template_id="invoice_reminder_v1",
        invoice_id="INV-2001",
        amount=4500,
        currency="INR",
    )

    template = EmailTemplate(
        template_id="invoice_reminder_v1",
        subject_template="Reminder: Invoice {invoice_id}",
        body_template="Invoice {invoice_id}: {currency} {amount}",
        required_variables=[
            "invoice_id",
            "currency",
            "amount",
        ],
    )

    consent = RecipientConsent(
        email="customer@example.com",
        consent_granted=True,
        unsubscribed=False,
    )

    provider = FakeEmailProvider()

    return email_input, template, consent, provider


def test_successful_invoice_reminder_delivery():
    email_input, template, consent, provider = create_task2_data()

    result = send_invoice_reminder(
        email_input,
        template,
        consent,
        provider,
        "TEST-EMAIL-001",
    )

    assert result.status == DeliveryStatus.SENT
    assert result.provider_message_id == "FAKE-MSG-0001"
    assert len(provider.sent_messages) == 1


def test_missing_template_variable():
    email_input, template, consent, provider = create_task2_data()

    template.required_variables.append("customer_name")

    with pytest.raises(ValueError, match="Missing template variables"):
        send_invoice_reminder(
            email_input,
            template,
            consent,
            provider,
            "TEST-EMAIL-002",
        )

    assert len(provider.sent_messages) == 0


def test_recipient_without_consent_is_rejected():
    email_input, template, consent, provider = create_task2_data()

    consent.consent_granted = False

    with pytest.raises(PermissionError, match="has not granted"):
        send_invoice_reminder(
            email_input,
            template,
            consent,
            provider,
            "TEST-EMAIL-003",
        )

    assert len(provider.sent_messages) == 0


def test_unsubscribed_recipient_is_rejected():
    email_input, template, consent, provider = create_task2_data()

    consent.unsubscribed = True

    with pytest.raises(PermissionError, match="unsubscribed"):
        send_invoice_reminder(
            email_input,
            template,
            consent,
            provider,
            "TEST-EMAIL-004",
        )

    assert len(provider.sent_messages) == 0


def test_future_email_is_scheduled_without_sending():
    email_input, template, consent, provider = create_task2_data()

    email_input.scheduled_at = (
        datetime.now(timezone.utc) + timedelta(hours=2)
    )

    result = send_invoice_reminder(
        email_input,
        template,
        consent,
        provider,
        "TEST-EMAIL-005",
    )

    assert result.status == DeliveryStatus.SCHEDULED
    assert result.scheduled_at is not None
    assert len(provider.sent_messages) == 0


def test_invalid_email_is_rejected():
    email_input, template, consent, provider = create_task2_data()

    email_input.recipient = "not-an-email"

    with pytest.raises(ValueError, match="Invalid recipient"):
        send_invoice_reminder(
            email_input,
            template,
            consent,
            provider,
            "TEST-EMAIL-006",
        )

    assert len(provider.sent_messages) == 0


def test_task2_fixture():
    result = run_task2_fixture()

    assert result["result"]["status"] == "sent"
    assert result["provider_message_count"] == 1
    assert result["provider_messages"][0]["recipient"] == (
        "customer@example.com"
    )


# ============================================================
# TASK 3 — FAILURE, RETRY AND REPLAY SAFETY TESTS
# ============================================================

from email_automation import (
    Task3FakeEmailProvider,
    TransientProviderError,
    PermanentProviderError,
    send_with_retry,
    run_task3_fixture,
)


def test_transient_failure_retries_and_succeeds():
    provider = Task3FakeEmailProvider(
        outcomes=["transient", "success"]
    )

    result = send_with_retry(
        provider,
        "customer@example.com",
        "Test subject",
        "Test body",
        "invoice:1001:reminder",
        max_attempts=3,
    )

    assert result["success"] is True
    assert result["status"] == "sent"
    assert result["attempts"] == 2
    assert len(provider.sent_messages) == 1


def test_permanent_failure_is_not_retried():
    provider = Task3FakeEmailProvider(
        outcomes=["permanent"]
    )

    result = send_with_retry(
        provider,
        "customer@example.com",
        "Test subject",
        "Test body",
        "invoice:1002:reminder",
        max_attempts=3,
    )

    assert result["success"] is False
    assert result["attempts"] == 1
    assert result["events"][-1]["event"] == "permanent_failure"
    assert provider.call_count == 1
    assert len(provider.sent_messages) == 0


def test_retries_stop_after_maximum_attempts():
    provider = Task3FakeEmailProvider(
        outcomes=["transient", "transient", "transient"]
    )

    result = send_with_retry(
        provider,
        "customer@example.com",
        "Test subject",
        "Test body",
        "invoice:1003:reminder",
        max_attempts=3,
    )

    assert result["success"] is False
    assert result["attempts"] == 3
    assert result["events"][-1]["event"] == "retry_exhausted"
    assert provider.call_count == 3


def test_timeout_is_retried():
    provider = Task3FakeEmailProvider(
        outcomes=["timeout", "success"]
    )

    result = send_with_retry(
        provider,
        "customer@example.com",
        "Test subject",
        "Test body",
        "invoice:1004:reminder",
        max_attempts=3,
    )

    assert result["success"] is True
    assert result["attempts"] == 2
    assert any(
        event["event"] == "timeout"
        for event in result["events"]
    )


def test_replay_does_not_send_duplicate_email():
    provider = Task3FakeEmailProvider()

    first = send_with_retry(
        provider,
        "customer@example.com",
        "Test subject",
        "Test body",
        "invoice:1005:reminder",
    )

    replay = send_with_retry(
        provider,
        "customer@example.com",
        "Test subject",
        "Test body",
        "invoice:1005:reminder",
    )

    assert first["success"] is True
    assert replay["success"] is True
    assert replay["message"]["replayed"] is True
    assert len(provider.sent_messages) == 1


def test_task3_fixture_prevents_duplicate_delivery():
    result = run_task3_fixture()

    assert result["first_result"]["success"] is True
    assert result["first_result"]["attempts"] == 2
    assert result["replay_result"]["success"] is True
    assert result["replay_result"]["message"]["replayed"] is True
    assert result["provider_message_count"] == 1
    assert result["duplicate_prevented"] is True


def test_invalid_retry_limit_is_rejected():
    provider = Task3FakeEmailProvider()

    try:
        send_with_retry(
            provider,
            "customer@example.com",
            "Test subject",
            "Test body",
            "invoice:1006:reminder",
            max_attempts=0,
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "at least 1" in str(exc)


def test_empty_idempotency_key_is_rejected():
    provider = Task3FakeEmailProvider()

    try:
        send_with_retry(
            provider,
            "customer@example.com",
            "Test subject",
            "Test body",
            " ",
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "idempotency_key" in str(exc)


# ============================================================
# TASK 4 — INTEGRATION AND OBSERVABILITY TESTS
# ============================================================

from email_automation import (
    EmailMetrics,
    FakeEmailGateway,
    Task3FakeEmailProvider,
    run_observed_email_delivery,
    run_task4_fixture,
)


def test_fake_gateway_implements_provider_contract():
    provider = Task3FakeEmailProvider()
    gateway = FakeEmailGateway(provider)

    result = gateway.send(
        recipient="customer@example.com",
        subject="Test",
        body="Test body",
        idempotency_key="test:gateway:001",
    )

    assert result["status"] == "sent"
    assert result["replayed"] is False
    assert len(provider.sent_messages) == 1


def test_observed_delivery_creates_structured_trace():
    provider = Task3FakeEmailProvider()
    gateway = FakeEmailGateway(provider)

    result = run_observed_email_delivery(
        gateway=gateway,
        recipient="customer@example.com",
        subject="Test",
        body="Test body",
        idempotency_key="test:trace:001",
        run_id="TEST-RUN-001",
        business_key="TEST-001",
    )

    trace = result["trace"]

    assert trace["trace_id"].startswith("TRACE-")
    assert trace["run_id"] == "TEST-RUN-001"
    assert trace["business_key"] == "TEST-001"
    assert trace["status"] == "sent"
    assert trace["completed_at"] is not None
    assert len(trace["events"]) >= 3


def test_metrics_track_successful_delivery():
    provider = Task3FakeEmailProvider()
    gateway = FakeEmailGateway(provider)
    metrics = EmailMetrics()

    result = run_observed_email_delivery(
        gateway=gateway,
        recipient="customer@example.com",
        subject="Test",
        body="Test body",
        idempotency_key="test:metrics:001",
        run_id="TEST-RUN-002",
        business_key="TEST-002",
        metrics=metrics,
    )

    assert result["metrics"]["total_runs"] == 1
    assert result["metrics"]["total_provider_attempts"] == 1
    assert result["metrics"]["successful_deliveries"] == 1
    assert result["metrics"]["failed_deliveries"] == 0


def test_metrics_track_retry_and_replay():
    result = run_task4_fixture()
    metrics = result["final_metrics"]

    assert metrics["total_runs"] == 2
    assert metrics["total_provider_attempts"] == 3
    assert metrics["successful_deliveries"] == 2
    assert metrics["failed_deliveries"] == 0
    assert metrics["retries"] == 1
    assert metrics["replays"] == 1


def test_observability_trace_records_retry_event():
    result = run_task4_fixture()

    events = [
        event["event"]
        for event in result["first_delivery"]["trace"]["events"]
    ]

    assert "transient_failure" in events
    assert "retry_scheduled" in events
    assert "delivery_succeeded" in events
    assert "delivery_completed" in events


def test_observability_replay_does_not_duplicate_delivery():
    result = run_task4_fixture()

    replay_events = [
        event["event"]
        for event in result["replay_delivery"]["trace"]["events"]
    ]

    assert "delivery_replayed" in replay_events
    assert result["provider_message_count"] == 1


def test_observability_rejects_invalid_retry_limit():
    provider = Task3FakeEmailProvider()
    gateway = FakeEmailGateway(provider)

    try:
        run_observed_email_delivery(
            gateway=gateway,
            recipient="customer@example.com",
            subject="Test",
            body="Test body",
            idempotency_key="test:invalid:001",
            run_id="TEST-RUN-003",
            business_key="TEST-003",
            max_attempts=0,
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "at least 1" in str(exc)

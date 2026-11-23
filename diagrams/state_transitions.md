
# Email Automation — Workflow State Diagram

```mermaid
stateDiagram-v2
    [*] --> created
    created --> validated: validate
    created --> cancelled: cancel

    validated --> scheduled: schedule
    validated --> queued: queue
    validated --> needs_review: block
    validated --> cancelled: cancel

    scheduled --> queued: queue
    scheduled --> cancelled: cancel

    queued --> running: start
    queued --> cancelled: cancel

    running --> sent: complete
    running --> failed: fail
    running --> needs_review: review

    failed --> queued: retry
    failed --> needs_review: review

    needs_review --> queued: retry
    needs_review --> cancelled: cancel

    sent --> [*]
    cancelled --> [*]
```

## State Descriptions

| State | Description |
|---|---|
| created | Workflow run has been initialized |
| validated | Initial input validation is complete |
| scheduled | Email is waiting for its scheduled time |
| queued | Email is ready for execution |
| running | Email delivery operation is in progress |
| sent | Email provider confirmed successful delivery acceptance |
| failed | An execution failure occurred |
| needs_review | Manual operator review is required |
| cancelled | Workflow was cancelled |

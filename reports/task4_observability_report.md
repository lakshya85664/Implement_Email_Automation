# Task 4 — Integration Boundary and Observability

## Scenario

provider_integration_with_observability

## Delivery Results

- First delivery status: sent
- Replay delivery status: sent
- Unique provider messages: 1

## Metrics

- Total workflow runs: 2
- Total provider attempts: 3
- Successful delivery outcomes: 2
- Failed delivery outcomes: 0
- Retries: 1
- Replays: 1

## Observability Evidence

- First delivery trace: `traces/task4_first_delivery_trace.json`
- Replay trace: `traces/task4_replay_trace.json`
- Structured summary: `outputs/task4_observability_summary.json`

## Verification

- Provider integration: PASS
- Structured tracing: PASS
- Retry observability: PASS
- Replay observability: PASS
- Duplicate delivery prevention: PASS

## Scope and Limitation

This assessment uses a local fake email provider. It demonstrates the
integration contract, retry tracking, replay handling, structured traces,
and metrics without connecting to an external email service.

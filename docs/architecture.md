# Architecture

This project is a local-first backend system that models an AWS-style event-driven order processing platform.

The current architecture is intentionally small. It focuses on clear boundaries between accepting work, storing state, processing queued work, and observing behavior.

## Architectural Goal

The local app is not trying to be production infrastructure yet.

It is trying to make the main backend/platform concepts visible:

- idempotent API requests
- asynchronous processing
- shared persistent state
- separate API and worker responsibilities
- observable service behavior
- future AWS service mapping

## System Shape

```text
Client
-> API layer
-> service layer
-> local JSON storage
-> local queue
-> worker runtime
-> order-processing pipeline
-> local JSON storage
```

## Responsibility Boundaries

| Area | Current responsibility |
| --- | --- |
| API | Accept HTTP requests, validate input, enforce idempotency, enqueue work |
| Worker | Poll/dequeue work and trigger one processing attempt |
| Pipeline | Coordinate business steps for an order |
| Services | Own focused business behavior such as inventory, payment, invoices, notifications |
| Storage | Persist local state in JSON files |
| Logging | Explain runtime behavior for humans |

## Business Truth vs Operational Visibility

The app separates state from visibility:

```text
JSON files -> business truth
logs       -> operational visibility
```

If the two disagree, storage is the current source of truth.

## Current Intentional Simplicity

The project does not yet have:

- repository/adapter boundaries
- broad dependency injection
- retry/backoff
- DLQ behavior
- full stored-record contracts
- AWS infrastructure

Those are planned later, after the local model is understandable.

## Local To AWS Mapping

| Local concept | Future AWS equivalent |
| --- | --- |
| FastAPI app | API Gateway + Lambda |
| Worker runtime | Lambda worker |
| JSON order storage | DynamoDB orders table |
| JSON idempotency storage | DynamoDB idempotency table |
| JSON queue | SQS |
| JSON inventory storage | DynamoDB inventory table |
| Invoice records/artifacts | S3 / DynamoDB metadata |
| Notification records | SNS / notification tracking |
| stdout logs | CloudWatch Logs |

## Direction

The planned direction is:

```text
contracts
-> repository / adapter boundary
-> explicit failure handling
-> retry / backoff
-> DLQ
-> behavior-focused tests
-> AWS infrastructure
```

## Related Docs

For detailed concepts, see:

- `docs/concepts/order-processing-flow.md`
- `docs/concepts/worker-model.md`
- `docs/concepts/storage-model.md`
- `docs/concepts/logging.md`
- `docs/concepts/configuration.md`
- `docs/concepts/failure-handling.md`

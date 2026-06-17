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
-> workflow / service layer
-> repositories
-> adapters
-> local JSON storage
-> local queue
-> worker runtime
-> order-processing workflow
-> repositories / adapters
```

## Responsibility Boundaries

| Area | Current responsibility |
| --- | --- |
| API | Accept HTTP requests, validate input, translate workflow/service results into HTTP responses |
| Workflows | Coordinate use cases such as order creation, worker decisions, and order processing |
| Worker | Poll/dequeue work and trigger processing through workflow code |
| Pipeline | Process one order attempt and coordinate business steps |
| Services | Own focused business behavior such as inventory, payment, invoices, notifications |
| Repository | Provide domain data access behind service/pipeline code |
| Adapter | Hide physical storage details and serialization |
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

The project has established:

- repository and JSON adapter boundaries for the current JSON-backed domains
- Pydantic objects at storage and service boundaries
- workflow classes for worker and order-processing orchestration
- lightweight dependency wiring for application entrypoints
- typed service, repository, and model contracts
- retry/backoff behavior for retryable payment and notification failures
- pipeline checkpoint guards for already completed side-effect steps
- behavior-focused tests grouped by purpose

The project does not yet have AWS infrastructure. Local DLQ simulation is also
intentionally skipped for now because SQS redrive policy should own DLQ movement
later.

## Repository / Adapter Direction

The repository/adapter boundary is now the current local storage pattern for the active JSON-backed domains.

```text
API / worker runtime
-> workflows
-> services
-> repository
-> JSON adapter
-> JSON storage helper
-> data/*.json
```

The goal is for business logic to work with validated Pydantic objects while adapters own JSON serialization and validation.

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

The current direction is:

```text
contracts
-> repository / adapter boundary
-> controlled workflow failure handling
-> retry / backoff
-> behavior-focused tests
-> cleanup / layer responsibility documentation
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
- `docs/concepts/repository-adapter.md`
- `docs/concepts/layer-responsibilities.md`

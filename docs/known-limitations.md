# Known Limitations

This project is a local learning implementation, not production infrastructure.
The limitations below define the boundary of the local MVP and the problems that
should be addressed through the AWS/platform phase rather than more local
simulation.

## Storage And Concurrency

- JSON files are the local source of truth, but they are not safe for concurrent
  writers.
- API and worker processes can race while reading and replacing the same file.
- Updates across orders, inventory, idempotency keys, invoices, notifications,
  and the queue are not transactional.
- There is no optimistic locking, conditional write, or atomic inventory update.
- Corrupt or unavailable storage is expected to fail loudly rather than recover
  automatically.

The AWS phase should replace these guarantees with DynamoDB conditional writes,
idempotent updates, and explicit decisions about transactions and consistency.

## Queue And Worker Model

- The processing queue is a JSON list of order IDs, not a message broker.
- It has no visibility timeout, acknowledgement lease, delivery counter, or
  native redelivery behavior.
- The current design assumes one effective worker and has no protection against
  concurrent consumers processing the same order.
- Retry backoff uses blocking `time.sleep()`, which should not be copied into a
  Lambda worker.
- Stale queue entries are discarded locally, but there is no operational replay
  mechanism.
- A local DLQ is intentionally not implemented.

The AWS phase should use SQS delivery semantics, Lambda invocation failure,
visibility timeout, and an SQS redrive policy with a DLQ.

## Retry And Workflow Reliability

- Payment capture and notification sending are the only retry paths covered by
  exhaustion and eventual-success behavior tests.
- `retryable_failure_steps` accepts valid `OrderFailureStep` values, but the
  configuration does not enforce that every selected step is actually safe to
  retry.
- Completed-step guards reduce duplicate inventory finalization, invoice
  creation, and notification sending, but a guard is not the same as atomic
  execution.
- A process can still fail after an external side effect succeeds but before its
  checkpoint is persisted.
- Inventory finalization and invoice creation still use broad exception catches.
- Compensation is intentionally narrow; payment retry exhaustion releases
  reserved inventory, but there is no general saga or rollback mechanism.

AWS integration should drive the next reliability decisions, especially around
duplicate delivery, conditional writes, idempotent side effects, and crash
windows.

## External Integrations

- Payment capture is a mock operation.
- Notification sending creates a local record rather than calling a provider.
- Invoices are JSON records rather than generated artifacts stored in S3.
- There is no API Gateway, Lambda, DynamoDB, SQS, SNS, EventBridge, CloudWatch,
  IAM policy, deployment pipeline, or rollback strategy yet.

These integrations should be added only when their concrete AWS behavior is
being implemented and tested.

## Testing And Operations

- The current suite focuses on deterministic unit and behavior tests.
- It does not exercise concurrent writers, multiple workers, load, network
  failures, AWS permissions, or deployed infrastructure.
- Logs are readable stdout text rather than structured CloudWatch events.
- There are no production metrics, alarms, traces, dashboards, or runbooks.

## Local MVP Freeze

The local architecture is considered complete after the documentation closeout.
Further local changes should require at least one concrete reason:

- an AWS integration exposes a boundary problem
- a test demonstrates incorrect behavior
- deployment or runtime behavior fails
- production delivery semantics require a change

Potential cleanliness improvements alone are not enough reason to continue
expanding the local implementation.

# Failure Handling

Failure handling is implemented for the current local workflow slice.

The current implementation makes workflow failures explicit in order state before adding retry or DLQ behavior.

## Current Goal

When something fails, the system should know:

```text
which order failed
which step failed
why it failed
what state was saved
whether anything needs to be released
```

## Failure Categories

Not every error belongs to the same layer.

```text
API / request validation failure
-> owned by FastAPI and Pydantic
-> return HTTP 4xx/422
-> do not create an order
-> do not enqueue work
-> do not involve the worker

Business workflow failure
-> owned by the order pipeline with help from services
-> order already exists
-> mark order FAILED
-> set failure_step
-> set failure_reason
-> save order state

Retryable operational failure
-> planned for retry/backoff work
-> examples: temporary payment or notification failure
-> not part of the first failure-handling slice

Poison or exhausted message
-> planned for DLQ work
-> move failed work into an inspectable dead-letter queue later

System / storage failure
-> local JSON infrastructure problem
-> fail loudly for now
-> do not hide corrupted local state behind broad catch-all handlers
```

## Current Workflow Failure Cases

```text
stale queue / missing order_id
inventory failure
payment failure
invoice failure
notification failure
```

The order pipeline handles the main workflow checkpoints:

```text
inventory reservation
payment capture
inventory sale finalization
invoice creation
notification sending
```

Inventory reservation is a business failure path. The inventory service marks the inventory step as failed and stores the reason, then the order pipeline turns that into a whole-order failure.

Inventory reservation validates all order items before mutating stock. If a later item has insufficient stock, earlier items are not partially reserved.

Stale queue messages are worker/queue consistency failures, not order failures. If a queued `order_id` no longer exists, the worker discards the stale queue message separately from empty queue handling.

Payment, inventory finalization, invoice, and notification currently use transitional broad exception handling in the pipeline. Later versions can replace those broad catches with named domain errors.

## Order Failure Fields

Orders include:

```text
failure_reason
failure_step
```

Retry work later may add:

```text
attempt_count
last_error
```

## Important Rule

Failure handling comes before retry/DLQ.

First make failures visible and deterministic. Then decide which failures should be retried.

For this failure-handling slice, the target is controlled order workflow failure state, not a complete reliability platform.

## Retry Thinking

Not every failure should be retried.

Examples:

```text
temporary payment failure      retry later
temporary notification failure retry later
invalid order data             do not retry forever
insufficient inventory         controlled failure
```

Retry belongs to a later version. The first version should only make the failure clear enough that retry policy can be added safely afterward.

## Inventory Compensation

If inventory was reserved and payment fails, the pipeline explicitly releases reserved inventory before saving the failed order state.

Later retry/DLQ work may make compensation policy more granular.

Inventory reservation itself avoids partial reservation by checking all requested items before changing stock.

## Logging

Failure logs should include at least:

```text
order_id
failure_step
failure_reason
```

## Do Not Do

- Do not hide failures only in logs.
- Do not retry everything.
- Do not lose the step where the failure happened.
- Do not leave reserved inventory stuck after a later failure.
- Do not turn API validation errors into worker failures.
- Do not keep broad catch-all handlers forever; replace them with named domain failures when the failure model stabilizes.

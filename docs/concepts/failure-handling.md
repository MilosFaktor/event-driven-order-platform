# Failure Handling

Failure handling is implemented for the current local workflow slice.

The current implementation makes workflow failures explicit in order state and
adds the first local retry/backoff behavior for selected retryable steps.

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
-> examples: temporary payment or notification failure
-> worker retries according to local retry/backoff settings
-> pipeline restarts from the failed retryable step

Poison or exhausted message
-> max retry attempts reached
-> current local behavior stops processing and dequeues the work
-> later DLQ work can move exhausted work into an inspectable dead-letter queue

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

Payment and notification failures use named domain errors in the current local retry slice.

Inventory finalization and invoice failures still use transitional broad exception handling in the pipeline. Later versions can replace those broad catches with named domain errors.

## Order Failure Fields

Orders include:

```text
failure_reason
failure_step
attempt_count
last_failure_step
last_error
```

Later retry/DLQ work may add:

```text
failure_code
failure_retryable
```

## Important Rule

Failure handling comes before DLQ.

First make failures visible and deterministic. Then retry only the failures that
are explicitly classified as retryable.

For the current local slice, the target is controlled workflow failure state plus
a small retry/backoff simulation, not a complete reliability platform.

## Retry Thinking

Not every failure should be retried.

Examples:

```text
temporary payment failure      retry
temporary notification failure retry
invalid order data             do not retry forever
insufficient inventory         controlled failure
```

Retryable steps are configured through `retryable_failure_steps`.

Current retryable steps:

```text
CAPTURE_PAYMENT
SEND_NOTIFICATION
```

Current worker behavior:

```text
completed order -> dequeue and stop
retryable failed order + attempts remaining -> wait using exponential backoff and retry
retryable failed order + max attempts reached -> dequeue and stop
non-retryable failed order -> dequeue and stop
stale queue message -> dequeue and stop
```

The order pipeline processes one attempt at a time. When retrying a failed order,
it uses the saved `failure_step` to restart from the failed retryable step.

## Recovered Failure State

When a retryable failure later succeeds, the active failure fields are cleared:

```text
failure_step = None
failure_reason = None
```

The previous failure remains inspectable as recovery metadata:

```text
last_failure_step
last_error
```

This keeps the current order state clear:

```text
COMPLETED means no active failure
last_error explains the previous failure that was recovered from
```

## Inventory Compensation

If inventory was reserved and payment fails, the pipeline keeps the reservation
during retry attempts. If payment still fails after the maximum number of
processing attempts, the pipeline releases the reserved inventory before saving
the exhausted failed state.

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

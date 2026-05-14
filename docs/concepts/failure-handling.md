# Failure Handling

Failure handling is not complete yet.

This doc captures the direction before adding random `try/except` blocks.

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
-> owned by workflow/services
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

## First Failure Cases

```text
stale queue / missing order_id
inventory failure
payment failure
invoice failure
notification failure
```

## Fields To Add

Orders will need:

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

For the first failure-handling version, the target is controlled order workflow failure state, not a complete reliability platform.

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

If inventory was reserved and a later step fails permanently, reserved inventory may need to be released.

That behavior should be explicit in the pipeline.

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
- Do not catch broad system/storage errors unless the app can save a meaningful state.

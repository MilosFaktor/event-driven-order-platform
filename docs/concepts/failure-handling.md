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

## Retry Thinking

Not every failure should be retried.

Examples:

```text
temporary payment failure      retry later
temporary notification failure retry later
invalid order data             do not retry forever
insufficient inventory         controlled failure
```

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

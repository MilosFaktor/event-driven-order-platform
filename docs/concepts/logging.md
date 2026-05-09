# Logging

Logging is how I inspect what the local system is doing at runtime.

Logs are not business truth. The JSON files currently hold the state. Logs just help explain what happened.

## Current Logger Names

```text
API                  request/response flow
worker.runtime       standalone worker lifecycle
worker.service       dequeue and process one order
orders.service       order record helpers
orders.pipeline      order processing workflow
idempotency.service  idempotency key lookup/storage
queue.service        queue mutations
inventory.service    inventory changes
payment.service      mock payment events
invoice.service      invoice creation
notification.service notification creation
```

## Current Style

Logs are simple key-value text:

```text
order_processing_pipeline_started order_id=ord_123
payment_captured order_id=ord_123
notification_sent order_id=ord_123 notification_id=ntf_ord_123
```

This is enough for the local version.

## Levels

```text
DEBUG    noisy internals, repeated saves, item-level movement
INFO     normal business milestones
WARNING  expected but problematic situations
ERROR    unexpected or inconsistent failures
```

## Rules For Now

- Important order-flow logs should include `order_id`.
- Do not log raw idempotency keys.
- Do not log secrets.
- Keep repeated internal details at `DEBUG`.
- Use logger names to show which part of the app produced the event.

## Future Direction

Later logs may become JSON/structured logs with fields like:

```text
order_id
correlation_id
step
status
attempt
failure_reason
```

The local stdout logging model maps naturally to CloudWatch later.

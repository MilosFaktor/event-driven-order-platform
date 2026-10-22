# Logging

Logging is how I inspect what the local system is doing at runtime.

Logs are not business truth. The JSON files currently hold the state. Logs just help explain what happened.

## Current Logger Names

```text
api                      request/response flow
worker.runtime           standalone worker lifecycle
worker.service           dequeue and process one order
create_order.workflow    create-order orchestration
order.pipeline           order processing workflow
order.service            order operations
idempotency.service      idempotency key lookup/storage
processing_queue.service queue mutations
inventory.service        inventory changes
payment.service          mock payment events
invoice.service          invoice creation
notification.service     notification creation

order.repo               order persistence
idempotency.repo         idempotency key persistence
processing_queue.repo    queue persistence
inventory.repo           inventory persistence
invoice.repo             invoice persistence
notification.repo        notification persistence
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

The layer does not determine the level. Repository events are normally `DEBUG`,
but service and workflow events can use any level appropriate to the event.

## Rules For Now

- Important order-flow logs should include `order_id`.
- Do not log raw idempotency keys.
- Do not log secrets.
- Keep repeated internal details at `DEBUG`.
- Keep repository reads, writes, and expected misses at `DEBUG`.
- Keep completed business actions and workflow milestones at `INFO`.
- Use `WARNING` for controlled failures and exhausted retries.
- Use `ERROR` when an unexpected exception or inconsistent state needs attention.
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

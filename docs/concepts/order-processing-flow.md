# Order Processing Flow

This is the current mental model for how one order moves through the local app.

## Flow

```text
POST /v1/orders
-> create PENDING order
-> store idempotency key
-> enqueue order_id
-> return response

worker/manual endpoint
-> peek queued order_id
-> load order
-> mark PROCESSING
-> reserve inventory
-> capture mock payment
-> finalize inventory sale
-> create invoice
-> send notification
-> mark COMPLETED
```

## Main Files

```text
app/api/main.py                       API layer
app/services/order_service.py          order records
app/services/idempotency_service.py    idempotency keys
app/services/queue_service.py          queue storage
app/workflows/worker_service.py        dequeue one order
app/workflows/order_pipeline_service.py processing workflow
```

## Rules For Now

- The API creates and queues work. It should not process the full order.
- The worker/workflow owns processing.
- The order workflow should save state after meaningful steps.
- Completed orders should not be processed again.
- Missing queued order IDs are treated as stale queue messages and discarded by the worker.
- Inventory reservation should not partially reserve earlier items when a later item fails.
- Retryable payment and notification failures can be retried with backoff.
- Successful retry recovery clears active failure state and preserves the previous failure in last-error metadata.
- Completed side-effect steps are guarded so re-entry does not duplicate inventory finalization, invoice creation, or notification sending.

## Retry And Re-Entry

The order pipeline uses two layers of protection:

```text
failure_step map -> chooses where retry starts
step status guard -> skips a step if its side effect already completed
```

Examples:

```text
FINALIZED inventory sale -> do not move stock again
CREATED invoice -> do not create invoice again
SENT notification -> do not send notification again
```

## Current States

```text
PENDING
PROCESSING
COMPLETED
FAILED
```

## Failure State

Failure handling records clearer fields like:

```text
failure_reason
failure_step
last_error
last_failure_step
```

Retry work tracks:

```text
attempt_count
```

The local flow is meant to map later to:

```text
API -> API Gateway/Lambda
queue -> SQS
worker -> Lambda worker
order state -> DynamoDB
redrive / DLQ -> SQS redrive policy + SQS DLQ
logs -> CloudWatch
```

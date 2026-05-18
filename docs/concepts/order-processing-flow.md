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
-> dequeue order_id
-> load order
-> mark PROCESSING
-> reserve inventory
-> capture mock payment
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
- Missing queued order IDs should become controlled failures later.

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
```

Retry work may later add:

```text
attempt_count
```

The local flow is meant to map later to:

```text
API -> API Gateway/Lambda
queue -> SQS
worker -> Lambda worker
order state -> DynamoDB
logs -> CloudWatch
```

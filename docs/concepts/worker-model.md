# Worker Model

The worker model explains how order processing happens outside the order creation request.

## Purpose

The API accepts work.

The worker processes work.

This keeps order creation separate from the longer business pipeline.

## Current Worker Modes

Manual worker endpoint:

```text
POST /v1/worker/process-next-order
```

This is useful for local debugging because one queued order can be processed on demand.

Standalone worker process:

```text
make worker
```

This is closer to the future AWS worker model.

## Current Flow

```text
queue contains order_id
-> worker peeks at the first order_id
-> worker calls OrderPipelineService for one processing attempt
-> worker retries configured failures with local blocking backoff
-> worker dequeues after success, stale work, non-retryable failure, or exhaustion
```

## Main Realization

The API process and worker process do not share memory.

If the API stores queued work only in memory, the standalone worker cannot see it.

That is why the local project uses JSON persistence for shared state.

## Main Files

```text
app/workflows/worker_service.py         queue decisions, retries, and outcomes
app/workers/order_worker.py             standalone worker runtime loop
app/services/queue_service.py           queue storage
app/workflows/order_pipeline_service.py one pipeline attempt and checkpoints
```

## Rules For Now

- `worker_service.py` should own queue decisions, retries, backoff, and terminal outcomes.
- `order_pipeline_service.py` should own one processing attempt and ordered business steps.
- `order_worker.py` should own the standalone worker loop.
- The worker should not create orders.
- The worker should not know API request details.
- Empty queue handling should be clean and explicit.

## Current Reliability Boundary

```text
implemented locally: stale-message handling, retry attempts, blocking backoff
deferred to AWS: visibility timeout, redelivery, DLQ, message metadata
```

## AWS Mapping

```text
standalone worker process -> Lambda worker mental model
local queue JSON          -> SQS mental model
order_id in queue         -> SQS message body
worker stdout logs        -> CloudWatch Logs
```


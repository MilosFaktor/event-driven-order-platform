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
make run-worker
```

This is closer to the future AWS worker model.

## Current Flow

```text
queue contains order_id
-> worker dequeues order_id
-> worker calls order_pipeline_service.process_order(order_id)
-> pipeline updates order state
```

## Main Realization

The API process and worker process do not share memory.

If the API stores queued work only in memory, the standalone worker cannot see it.

That is why the local project uses JSON persistence for shared state.

## Main Files

```text
app/services/worker_service.py          dequeue one order and call pipeline
app/workers/order_worker.py             standalone worker runtime loop
app/services/queue_service.py           queue storage
app/services/order_pipeline_service.py  order processing workflow
```

## Rules For Now

- `worker_service.py` should stay focused on dequeueing one order and calling the pipeline.
- `order_worker.py` should own the standalone worker loop.
- The worker should not create orders.
- The worker should not know API request details.
- Empty queue handling should be clean and explicit.

## Future Work

```text
stale queue handling
retry attempts
backoff
DLQ
queue message model instead of plain order_id
```

## AWS Mapping

```text
standalone worker process -> Lambda worker mental model
local queue JSON          -> SQS mental model
order_id in queue         -> SQS message body
worker stdout logs        -> CloudWatch Logs
```


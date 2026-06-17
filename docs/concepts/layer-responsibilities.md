# Layer Responsibilities

This document explains what each layer in the local application is responsible
for. The goal is to keep the project understandable as the local implementation
moves toward an AWS-backed version.

Current direction:

```text
API / worker runtime
-> workflows
-> services
-> repositories
-> adapters
-> json_storage
-> data/*.json
```

## API Layer

The API layer is the transport boundary.

Belongs here:

- FastAPI route functions
- HTTP request validation
- response models for client-facing output
- HTTP status code selection
- `HTTPException` translation
- calling application workflows or simple services

Does not belong here:

- multi-step business orchestration
- retry/backoff decisions
- direct JSON file access
- repository/adapter details
- payment, inventory, invoice, or notification business rules

Current example:

```text
POST /v1/orders
-> accepts HTTP request
-> calls CreateOrderWorkflow
-> translates workflow result into HTTP response
```

## Workflows

Workflows coordinate use cases that involve more than one focused service or
decision.

Belongs here:

- ordering multiple business steps
- coordinating services
- deciding one use-case flow
- returning internal result dataclasses
- saving workflow-level state

Does not belong here:

- FastAPI `Response` or `HTTPException`
- raw JSON serialization
- low-level storage mechanics

Current examples:

```text
CreateOrderWorkflow
-> idempotency lookup
-> order creation
-> idempotency save
-> queue enqueue
```

```text
WorkerService
-> inspect queue
-> call OrderPipelineService
-> decide retry, stop, or dequeue
```

```text
OrderPipelineService
-> run one processing attempt
-> choose start step
-> execute order pipeline steps
-> save order success/failure state
```

## Services

Services own focused business actions.

Belongs here:

- order storage operations through repositories
- queue operations through repositories
- inventory reservation, release, and finalization
- mock payment capture
- invoice creation
- notification creation
- idempotency key lookup/storage

Does not belong here:

- HTTP status codes
- route handling
- full application use-case orchestration
- cross-service retry loops

Examples:

```text
InventoryService reserves stock.
PaymentService captures payment.
InvoiceService creates invoice records.
NotificationService creates notification records.
```

## Repositories

Repositories provide domain data access behind services and workflows.

Belongs here:

- load/save/list operations for one domain concept
- stable interface used by services
- hiding adapter details from business logic

Does not belong here:

- HTTP concerns
- business workflow decisions
- raw endpoint behavior

Current repository-backed domains:

```text
orders
inventory
processing queue
idempotency keys
invoices
notifications
```

## Adapters

Adapters implement concrete persistence.

Belongs here:

- JSON file read/write implementation
- serialization/deserialization
- Pydantic validation at the storage boundary
- mapping between storage files and model objects

Does not belong here:

- API route behavior
- retry policy
- business process decisions

Current adapter type:

```text
JSON adapters
```

Future adapter direction:

```text
JSON adapter -> DynamoDB adapter / SQS adapter / S3 adapter
```

## Models

Models define structured data and validation.

Belongs here:

- Pydantic domain/storage models
- request models
- response models
- enums for known states
- assignment validation for model state

Does not belong here:

- service orchestration
- storage access
- HTTP route logic

Current examples:

```text
Order
OrderSteps
CreateOrderRequest
CreateOrderResponse
Inventory
Invoice
Notification
ProcessingQueue
```

Enums live in:

```text
app/models/enums.py
```

## Storage

Storage is the current local source of truth.

Belongs here:

- JSON files under `data/`
- generic JSON load/save helpers

Does not belong here:

- business rules
- route logic
- workflow decisions

Current storage files:

```text
data/orders.json
data/idempotency_keys.json
data/processing_queue.json
data/inventory.json
data/invoices.json
data/notifications.json
```

## Tests

Tests are grouped by purpose.

Current structure:

```text
tests/unit
tests/behavior
tests/integration
```

`tests/unit` belongs to small isolated rules:

- enum values
- retry policy calculation
- future model validation rules

`tests/behavior` belongs to business and API behavior:

- create-order API behavior
- worker decisions
- pipeline happy path
- pipeline retry behavior
- pipeline idempotency guards
- inventory failure behavior

`tests/integration` is reserved for future cross-layer local flows:

- API creates order, queue receives order ID, worker processes order
- JSON storage is intentionally part of the scenario

## Current Design Rules

Use a workflow when the operation coordinates multiple responsibilities.

```text
Create order = workflow
```

Reason:

```text
idempotency lookup
order creation
idempotency save
queue enqueue
HTTP response translation
```

Use a direct service call when the operation is a simple read.

```text
Get order = service call is enough
List orders = service call is enough for now
```

Keep result objects internal.

```text
CreateOrderResult = workflow result
WorkerProcessResult = worker result
CreateOrderResponse = API response model
```

Keep HTTP concerns at the API boundary.

```text
workflow returns what happened
API decides how HTTP represents it
```

Keep retry ownership clear.

```text
WorkerService decides retry/backoff.
OrderPipelineService processes one attempt.
Domain services perform focused work.
```

## AWS Direction

The local layers are designed so AWS can replace infrastructure without
rewriting the business flow.

Expected mapping:

```text
FastAPI route        -> API Gateway / Lambda handler
JSON order adapter   -> DynamoDB adapter
JSON queue adapter   -> SQS
worker loop          -> Lambda triggered by SQS
stdout logs          -> CloudWatch Logs
local env settings   -> Parameter Store / Secrets Manager
```

The intended rule stays the same:

```text
Cloud handlers stay thin.
Business logic stays in workflows and services.
```

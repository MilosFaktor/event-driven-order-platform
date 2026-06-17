# Version History

This document tracks the local Phase 1 evolution of the Event-Driven Order Processing Platform. It is reconstructed from development logs and is intended as a public reference for previous unpublished versions.

## v0.1.0 - Python Core Order Flow

Goal: prove the basic order-processing logic without a web framework.

Changes:

- Created the initial local order flow in Python.
- Added in-memory order and inventory dictionaries.
- Created a fake order and processed it through basic status changes.
- Added simple inventory handling and failure behavior.
- Established the first tagged project milestone.

Why it mattered:

This version proved the core business idea before introducing API, persistence, or infrastructure concerns.

## v0.2.0 - Clean Project Structure

Goal: split the initial script into a clearer application structure.

Changes:

- Moved order logic out of `main.py`.
- Introduced separate application folders for services, storage, and models.
- Kept `main.py` focused on orchestration/entry-point behavior.

Why it mattered:

This created the first maintainable project shape and prepared the app for FastAPI.

## v0.2.1 - Ruff CI And Branch Protection

Goal: add basic quality checks and protect the main branch.

Changes:

- Added Ruff linting/formatting workflow.
- Added required checks before merging to `main`.
- Configured branch protection for `main`.
- Tagged the quality-check milestone.

Why it mattered:

This introduced early engineering discipline: small branches, CI checks, protected merges, and tagged versions.

## v0.3.0 - FastAPI Basic API

Goal: expose the order system through HTTP.

Changes:

- Added FastAPI and Uvicorn.
- Added `POST /v1/orders`.
- Added `GET /v1/orders/{order_id}`.
- Added Pydantic request models for order creation.
- Added example request JSON under `examples/requests`.
- Added Makefile commands for running the API and creating test orders.
- Kept order creation asynchronous in spirit: the API creates a `PENDING` order and returns without processing it.

Why it mattered:

This turned the local Python logic into a usable backend API while preserving the assignment's core rule: the API accepts work, it does not process the full order.

## v0.3.1 - UUID Order IDs

Goal: improve order ID generation.

Changes:

- Replaced simple sequential order IDs with UUID-based order IDs.
- Added lookup protection so generated IDs do not collide with existing orders.

Why it mattered:

This moved the project closer to realistic backend ID generation.

## v0.4.0 - Idempotency

Goal: make order creation retry-safe.

Changes:

- Required the `Idempotency-Key` header on `POST /v1/orders`.
- Added in-memory idempotency key storage.
- Stored `idempotency_key -> order_id` mappings.
- Returned the existing order response when the same idempotency key is reused.
- Added helper/debug endpoints and Makefile commands for inspecting local state.

Why it mattered:

This implemented a core backend reliability pattern: client retries should not create duplicate orders.

## v0.5.0 - Local Queue Producer

Goal: introduce the producer side of local event-driven processing.

Changes:

- Added an in-memory `processing_queue`.
- Updated `POST /v1/orders` so new orders are queued after creation.
- Ensured duplicate idempotency-key requests do not enqueue duplicate work.
- Added a queue service/helper.
- Added a debug endpoint for inspecting the processing queue.

Why it mattered:

This separated order creation from order processing and introduced the local equivalent of publishing work to a queue.

## v0.5.1 - Manual Worker Processing

Goal: process queued orders manually through an endpoint.

Changes:

- Added `worker_service.process_next_order`.
- Added `POST /v1/worker/process-next-order`.
- The worker pops one `order_id` from the processing queue and calls `process_order`.
- Added a Makefile command for manually processing the next queued order.
- Added a guard so completed orders are not processed again.

Why it mattered:

This introduced the consumer side of the local queue flow without background loops or concurrency complexity.

## v0.5.2 - Split Processing Logic

Goal: make the order-processing pipeline real and readable.

Changes:

- Moved pipeline experimentation into an `experiments` sandbox.
- Split inventory logic into `inventory_service`.
- Updated inventory state to track:
  - `available_stock`
  - `reserved_stock`
  - `sold_stock`
- Refactored `process_order` into a pipeline orchestrator.
- Added invoice creation with item snapshots.
- Added notification creation.
- Added in-memory invoice and notification records.
- Added debug endpoints and Makefile helpers for invoices and notifications.

Pipeline at this point:

```text
order created
-> queued
-> worker processes order
-> reserve inventory
-> capture mock payment
-> finalize inventory sale
-> create invoice record
-> create notification record
-> mark order completed
```

Why it mattered:

This transformed `process_order` from a single blob of logic into a business pipeline with explicit steps and state changes.

## v0.5.3 - Standalone Worker Process Experiment

Goal: prove that the API process and worker process do not share memory.

Changes:

- Added a standalone worker process experiment.
- Added worker polling interval configuration.
- Ran the FastAPI API and worker process at the same time.
- Confirmed that API-created in-memory queue items are not visible to the worker process.

Lesson:

```text
Same code import does not mean shared runtime memory.
Separate processes need shared external state.
```

Why it mattered:

This proved why the real architecture needs external shared services such as SQS and DynamoDB, and why the local version needed persistent storage.

## v0.5.4 - JSON Persistent Storage

Goal: solve local API/worker shared-state problems using JSON files.

Changes:

- Added a `data/` folder for local JSON-backed state.
- Added JSON files for:
  - orders
  - idempotency keys
  - processing queue
  - inventory
  - invoices
  - notifications
- Added `json_storage` helpers for loading and saving JSON files.
- Wired `processing_queue` to `data/processing_queue.json`.
- Refactored `queue_service` with JSON-backed enqueue/dequeue helpers.
- Wired orders to `data/orders.json`.
- Wired idempotency keys to `data/idempotency_keys.json`.
- Wired invoices to `data/invoices.json`.
- Wired notifications to `data/notifications.json`.
- Wired inventory to `data/inventory.json`.
- Added `save_order(order)` to centralize single-order persistence.
- Changed marker/state helper functions to mutate only.
- Made `process_order` control when order state is saved between pipeline steps.
- Moved payment mock logic into `payment_service.py`.
- Added a reset/seed script for local JSON data.
- Added a Makefile command for resetting local JSON state.

Why it mattered:

This made the local API and worker process share state through files, mirroring the architectural role that DynamoDB, SQS, S3, and SNS will eventually play in AWS.

Current local shared state:

```text
orders              -> data/orders.json
idempotency keys    -> data/idempotency_keys.json
processing queue    -> data/processing_queue.json
inventory           -> data/inventory.json
invoices            -> data/invoices.json
notifications       -> data/notifications.json
```

## v0.5.5 - Local Logging And Observability

Goal: make the local API and worker flow observable through structured logs.

Changes:

- Moved shared logging setup into `app/core/logging_config.py`.
- Added API logs for order creation requests, idempotency matches, returned responses, order reads, and manual worker processing.
- Added worker runtime logs for startup, queue detection, and debug heartbeats.
- Added worker service logs for dequeueing and processing one queued order.
- Split order logging into:
  - `orders.service` for order creation, idempotency, loading, and saving helpers.
  - `orders.pipeline` for the multi-step order processing workflow.
- Added service-level logs for:
  - `queue.service`
  - `inventory.service`
  - `payment.service`
  - `invoice.service`
  - `notification.service`
- Replaced old `print()` statements in the service flow with logger calls.
- Tuned noisy internal details, such as repeated order saves and inventory item movements, to `DEBUG`.

Why it mattered:

This made the local system easier to understand and debug while preparing the project for future CloudWatch-style observability in AWS.

Example local trace:

```text
API creates a pending order
-> queue.service enqueues the order
-> worker.runtime detects work
-> worker.service dequeues the order
-> orders.pipeline starts processing
-> inventory.service reserves/finalizes stock
-> payment.service captures mock payment
-> invoice.service creates invoice record
-> notification.service creates notification record
-> orders.pipeline marks the order completed
```

## v0.5.6 - Config And Environment Settings

Goal: centralize local runtime settings and local run behavior.

Changes:

- Added Pydantic Settings in `app/core/config.py`.
- Added environment-based settings for:
  - `ENVIRONMENT`
  - `LOG_LEVEL`
  - `QUEUE_INTERVAL`
- Added `.env.example` with safe runnable defaults.
- Kept `.env.local` and `.env.prod` private/ignored for local and prod-like runs.
- Wired logging level to settings instead of a hardcoded logging constant.
- Wired worker queue interval to settings.
- Added Makefile targets for private local and prod-like API/worker runs.

Why it mattered:

This moved runtime behavior out of scattered hardcoded values and into one clear configuration layer. The local app can now run with safe defaults while still supporting private local and prod-like overrides.

## v0.5.7 - Service Cleanup

Goal: clean responsibility boundaries before failure handling.

Changes:

- Extracted idempotency logic into `idempotency_service.py`.
- Added an `idempotency.service` logger.
- Extracted the order processing workflow into `order_pipeline_service.py`.
- Kept `order_service.py` focused on order creation, loading, saving, and ID generation.
- Kept `worker_service.py` focused on dequeueing one order and calling the processing pipeline.

Why it mattered:

This made the codebase easier to extend without jumping into repository, adapter, dependency-injection, failure-handling, or retry work too early. The order pipeline is now isolated in the place where future failure handling, retry logic, and compensation behavior will naturally live.

Current local service boundaries:

```text
orders.service        -> order records and persistence helpers
idempotency.service   -> idempotency key records
orders.pipeline       -> order processing workflow
worker.service        -> dequeue one order and invoke the pipeline
queue.service         -> JSON queue operations
inventory.service     -> inventory reservation/finalization
payment.service       -> mock payment capture
invoice.service       -> invoice record creation
notification.service  -> notification record creation
```

## v0.5.8 - Architecture Docs Foundation

Goal: capture architecture concepts before deeper implementation.

Changes:

- Added `docs/architecture.md` as a high-level map of the local system shape, responsibility boundaries, and AWS direction.
- Added concept documentation for the current order-processing flow.
- Added concept documentation for the worker model.
- Added concept documentation for the storage model.
- Added concept documentation for logging.
- Added concept documentation for configuration.
- Added failure-handling direction before implementing retry or DLQ behavior.
- Added a local order pipeline diagram source under `docs/diagrams/local-order-pipeline.drawio`.
- Added the exported diagram image under `docs/screenshots/00-diagram.png`.
- Documented current local behavior, future AWS mapping, and known boundaries across the concept docs.

Why it mattered:

This version made the project easier to reason about before adding more moving parts. The docs now act as guardrails for future work on contracts, repository/adapter boundaries, failure handling, retries, DLQ behavior, and AWS migration.

Current concept docs:

```text
docs/architecture.md
docs/concepts/order-processing-flow.md
docs/concepts/worker-model.md
docs/concepts/storage-model.md
docs/concepts/logging.md
docs/concepts/configuration.md
docs/concepts/failure-handling.md
```

Diagram artifacts:

```text
docs/diagrams/local-order-pipeline.drawio
docs/screenshots/00-diagram.png
```

## v0.5.9 - Contract Models Foundation

Goal: define system data shapes before failure, retry, and DLQ complexity grows.

Changes:

- Added Pydantic contract models for stored order records.
- Added order item and order step models.
- Added inventory item and inventory root models.
- Added invoice and invoice item models.
- Added notification and notification root models.
- Added idempotency key and processing queue root models.
- Tightened create-order request validation with allowed currency values and non-empty item checks.
- Added validation rules for SKU prefixes, generated record ID prefixes, allowed statuses, and allowed step values.
- Wired RootModel validation into JSON-backed service boundaries:
  - orders
  - inventory
  - invoices
  - notifications
  - idempotency keys
  - processing queue
- Validated JSON data on load and before save while keeping current service callers working with plain dictionaries.
- Added clearer order state logging for pipeline checkpoints.
- Reduced repeated inventory writes during reservation and sale finalization.
- Stored invoice line totals as generated invoice snapshot data and validated them against quantity and unit price.

Why it mattered:

This version introduced explicit contracts around the local business data without rewriting the whole app around Pydantic objects. The service layer still works with dictionaries, but JSON-backed state now passes through validation at the main storage boundaries.

The work also made the next architecture step clearer: services now contain business behavior plus load/validate/save details, which shows why the future repository/adapter boundary in `v0.6.0` is useful.

Current contract model files:

```text
app/models/order.py
app/models/inventory.py
app/models/invoices.py
app/models/notifications.py
app/models/idempotency_keys.py
app/models/processing_queue.py
app/models/orders_request.py
```

Validation boundary pattern:

```text
load JSON
-> validate with Pydantic model / RootModel
-> return plain dict/list to current service code

update domain data
-> validate before save
-> save validated data back to JSON
```

Not included:

```text
- repository/adapter implementation
- dependency injection rewrite
- full pipeline conversion to Pydantic objects
- stale queue / orphaned order handling
- retry/backoff
- DLQ
```

## Completed Work - v0.6.0 Repository / Adapter Foundation

Goal: introduce a storage boundary before failure handling, retries, and broader tests.

Current finalization direction:

- Keep API and worker runtime code talking through services/workflows.
- Keep workflows focused on orchestration.
- Keep services focused on domain behavior.
- Keep repositories focused on domain data access.
- Keep adapters focused on JSON storage paths, serialization, and Pydantic validation.
- Use clearer naming:
  - `list_*` for collection reads
  - `get_*` for single-record lookups
- Prefer loading collections once, mutating in memory, and saving once when processing multiple items.

Implemented in v0.6.0:

```text
- JSON adapters and repositories for orders, inventory, queue, idempotency keys, invoices, and notifications
- service wiring through repositories instead of direct json_storage access
- workflow classes for worker and order processing orchestration
- lightweight AppDependencies container for top-level service wiring
- PaymentService class
- shared Currency type alias
- tighter type hints across service, repository, and model boundaries
```

Current v0.6.0 architecture shape:

```text
API / worker runtime
-> workflows
-> services
-> repositories
-> adapters
-> json_storage
-> data/*.json
```

Completed v0.6.0 slices:

```text
v0.6.0 - Order Repository Adapter Slice
v0.6.0 - Inventory Repository Adapter Slice
v0.6.0 - Queue Repository Adapter Slice
v0.6.0 - Idempotency Repository Adapter Slice
v0.6.0 - Invoice Repository Adapter Slice
v0.6.0 - Notification Repository Adapter Slice
v0.6.0 - Service Dependency Container
v0.6.0 - Payment Service Class Wiring
v0.6.0 - Worker and Pipeline Service Classes
v0.6.0 - Workflow Organization and Service Typing Cleanup
```

## v0.6.1 - Failure Handling

Goal: make order workflow failures explicit, deterministic, and saved before adding retry or DLQ behavior.

Implemented in v0.6.1:

```text
- failure_step added to order state alongside failure_reason
- order pipeline helper for central failed-order marking
- inventory reservation failure records inventory step failure and reason
- inventory reservation checks all items before mutating stock to prevent partial reservations
- payment failure path marks order failed and releases reserved inventory
- inventory sale finalization failures are handled in the pipeline
- invoice creation failures are handled in the pipeline
- notification sending failures are handled in the pipeline
- stale queued order IDs are discarded separately from empty queue handling
- broad transitional exception handling exists at workflow boundaries
```

Current responsibility shape:

```text
services perform domain work
order pipeline orchestrates steps and owns whole-order failure state
repositories/adapters persist local JSON state
```

## v0.6.2 - Retry / Backoff Simulation Foundation

Goal: add the first local retry/backoff behavior for retryable workflow failures.

Implemented in v0.6.2:

```text
- retry/backoff settings for max attempts, base delay, multiplier, and retryable steps
- attempt_count on orders
- FailureStep enum values aligned with exact pipeline checkpoints
- OrderSteps fields aligned with exact pipeline checkpoints
- named payment and notification failure exceptions
- worker-owned retry/backoff orchestration
- order-pipeline-owned single-attempt processing
- ordered pipeline step list
- step handler map in OrderPipelineService
- retry start position based on saved failure_step
- payment failures retry from CAPTURE_PAYMENT
- notification failures retry from SEND_NOTIFICATION
- payment failures keep inventory reserved during retry attempts
- inventory release after payment retries are exhausted
- pytest coverage for retry delay, happy path, payment retry exhaustion, and notification retry exhaustion
- GitHub Actions workflow for Ruff and pytest
```

Current retry behavior:

```text
completed order -> dequeue and stop
retryable failed order + attempts remaining -> wait using backoff and retry
retryable failed order + max attempts reached -> dequeue and stop
non-retryable failed order -> dequeue and stop
stale queue message -> dequeue and stop
```

Current retryable workflow steps:

```text
CAPTURE_PAYMENT
SEND_NOTIFICATION
```

Why it mattered:

This version moved the project from visible failure state into controlled retry
behavior. The worker now decides whether to retry, while the order pipeline
decides how one attempt runs and where a retry should resume.

Remaining limitations:

```text
- DLQ behavior is not implemented yet
- inventory finalization and invoice failure handling still use transitional broad catches
- local queue behavior is still a learning model, not a full SQS visibility-timeout simulation
```

## v0.6.3 - Retry Eventual Success

Goal: prove retryable temporary failures can recover and complete successfully.

Implemented in v0.6.3:

```text
- payment fail-once-then-success test
- notification fail-once-then-success test
- test doubles for temporary payment and notification failures
- recovered orders clear active failure_step and failure_reason
- previous failure metadata is preserved in last_failure_step and last_error
- retry recovery tests for payment and notification
```

Current recovered order behavior:

```text
temporary retryable failure happens
-> order is saved as FAILED with failure_step and failure_reason
-> worker retries from the failed checkpoint
-> retry succeeds
-> order is saved as COMPLETED
-> active failure_step / failure_reason are cleared
-> previous failure is preserved as last_failure_step / last_error
```

Why it mattered:

v0.6.2 proved retry exhaustion. v0.6.3 proved retry recovery.

## v0.6.4 - Pipeline Checkpoint Idempotency

Goal: make the pipeline safer to re-enter without duplicating side effects.

Implemented in v0.6.4:

```text
- reserve inventory skips when inventory is already RESERVED
- reserve inventory skips when inventory was already RELEASED
- payment capture skips when payment is already CAPTURED
- inventory sale finalization skips when inventory sale is already FINALIZED
- invoice creation skips when invoice is already CREATED
- notification sending skips when notification is already SENT
- payment failure avoids releasing already RELEASED inventory again
- tests prove inventory finalization is not applied twice
- tests prove notification sending is not applied twice
- tests prove invoice creation is not applied twice
```

Why it mattered:

```text
FailureStep map decides where retry should start.
Step guards decide whether a reached step should actually run.
```

This reduces duplicate side-effect risk when a saved order re-enters the
pipeline from an already completed checkpoint.

DLQ decision:

Local DLQ simulation is intentionally not implemented before MVP. In the future
AWS version, SQS redrive policy should move exhausted messages to a DLQ. The
application should focus on saving useful order failure state and metadata.

## v0.7.0 - Behavior-Focused Tests

Goal: add broader behavior coverage before reshaping the create-order API and
workflow boundaries.

Implemented in v0.7.0:

```text
- create-order API behavior tests
- request validation coverage for missing Idempotency-Key
- request validation coverage for invalid create-order bodies
- valid create-order request returns a PENDING saved order
- created order ID is added to the processing queue
- duplicate Idempotency-Key returns the existing order
- duplicate Idempotency-Key does not enqueue duplicate queued work
- WorkerService decision tests
- empty queue returns None
- stale/orphan queue item is discarded
- non-retryable failed order dequeues and stops without retry
- inventory reservation failure tests
- reservation failure marks the order FAILED at RESERVE_INVENTORY
- reservation failure leaves later pipeline steps PENDING
- reservation failure does not partially reserve earlier valid items
- shared test helpers for storage reset and default order creation
- narrow WorkerService protocols for queue-like and pipeline-like dependencies
```

Why it mattered:

```text
The project now has behavior tests around the client-facing API boundary,
worker decision logic, retry behavior, checkpoint idempotency, and inventory
reservation failure behavior.
```

This creates a safer base for the next cleanup: moving create-order orchestration
out of the FastAPI route while keeping the public API behavior stable.

Testing direction:

```text
Test behavior and contracts, not every implementation line.
Use shared helpers only for boring repeated setup.
Keep behavior-specific setup inline when it explains the scenario.
```

## v0.8.0 - Create Order Workflow Cleanup

Goal: make the create-order API route a thinner HTTP boundary.

Implemented in v0.8.0:

```text
- introduced CreateOrderWorkflow
- moved idempotency lookup, order creation, idempotency save, and queue enqueue into the workflow
- added CreateOrderResult dataclass for internal workflow output
- added CreateOrderResponse Pydantic model for API output
- kept FastAPI HTTP concerns inside the API layer
- kept create-order behavior tests passing
```

Why it mattered:

```text
The API now translates HTTP.
The workflow coordinates the use case.
```

## v0.8.1 - Worker Process Result Cleanup

Goal: replace loose worker return values with an explicit result object.

Implemented in v0.8.1:

```text
- added WorkerProcessResult
- added WorkerProcessResultOutcome
- replaced mixed WorkerService returns such as None, string sentinels, and raw orders
- manual worker API now translates worker outcomes explicitly
- worker behavior tests assert structured outcomes
```

Why it mattered:

WorkerService now returns one consistent shape. Callers can first inspect the
outcome and then decide how to represent it.

## v0.8.2 - Order Model Hardening

Goal: reduce stringly typed model state.

Implemented in v0.8.2:

```text
- introduced app/models/enums.py
- added Currency enum
- added OrderStatus enum
- renamed failure-step direction to OrderFailureStep
- added step-specific status enums
- added enum-backed invoice and notification statuses
- updated internal services and tests to use enum values
- kept API request/response tests string-based at the boundary
```

Why it mattered:

Internal model state became harder to accidentally misspell or assign
incorrectly while preserving normal JSON API behavior.

## v0.8.3 - Test Organization Cleanup

Goal: make the growing test suite easier to scan and reason about.

Implemented in v0.8.3:

```text
- moved API, worker, pipeline, and inventory behavior tests under tests/behavior
- split order pipeline tests into happy path, retry behavior, and idempotency guard modules
- moved small enum and retry policy checks under tests/unit
- reserved tests/integration for future cross-layer local JSON flows
- kept the full pytest suite passing
```

Current test grouping:

```text
tests/unit       -> small isolated checks
tests/behavior   -> API and business behavior
tests/integration -> future cross-layer local storage flows
```

Why it mattered:

The project now has enough tests that file organization affects understanding.
The split is based on cognitive load, not abstract test taxonomy.

## Next Versions

Current and planned next steps:

- `v0.8.4` - layer responsibility documentation
- dependency wiring cleanup
- logger naming / observability polish
- public README/docs polish
- future AWS SQS / DLQ integration
- `v1.0.0` - local Phase 1 MVP complete

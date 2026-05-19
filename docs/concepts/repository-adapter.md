# Repository / Adapter

Repository and adapter boundaries separate business logic from physical storage details.

The current local app uses JSON files as its storage backend. Earlier versions let services load, validate, and save JSON data directly. That worked for the first local MVP, but it made services responsible for both business decisions and storage mechanics.

## Current Shape

The project currently uses this boundary for the active JSON-backed domains.

```text
API / worker runtime
-> workflows
-> services
-> repository
-> adapter
-> JSON storage helper
-> data/*.json
```

Example order domain:

```text
order business logic
-> OrderRepository
-> JsonOrderAdapter
-> data/orders.json
```

## Responsibilities

| Layer | Responsibility |
| --- | --- |
| Service / pipeline | Business use cases and workflow decisions |
| Repository | Domain data access such as get/save/list orders |
| Adapter | Physical storage implementation and serialization boundary |
| Storage helper | Generic file read/write behavior |

## Pydantic Object Boundary

The app is moving toward keeping validated Pydantic objects at service and storage boundaries.

That means the adapter owns conversion at the storage edge:

```text
JSON dict
-> Order / Orders model
-> business logic works with objects
-> adapter dumps model back to JSON-safe data
```

This avoids repeatedly converting between dictionaries and models inside business logic.

## Why This Matters

The boundary makes future changes easier:

- JSON storage can later be replaced by DynamoDB with less service-layer churn.
- Tests can use in-memory repositories/adapters.
- Services can focus on business behavior.
- Storage validation and serialization live closer to the storage implementation.

## Current Limitations

This is still a local-first implementation, not production infrastructure.

For now:

- repositories/adapters are JSON-backed
- dependency wiring is intentionally lightweight
- failure handling is implemented for the current local workflow slice
- stale queue messages are discarded as non-order workflow failures
- retry/backoff and DLQ behavior remain later work

The goal is to keep business behavior separated from storage mechanics while adding reliability features one slice at a time.

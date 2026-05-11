# Repository / Adapter

Repository and adapter boundaries separate business logic from physical storage details.

The current local app uses JSON files as its storage backend. Earlier versions let services load, validate, and save JSON data directly. That worked for the first local MVP, but it made services responsible for both business decisions and storage mechanics.

## Current Direction

The project is now introducing the boundary gradually, starting with orders.

```text
API / worker
-> service / pipeline
-> repository
-> adapter
-> JSON storage helper
-> data/*.json
```

The first slice is the order domain:

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

The order slice is moving toward keeping `Order` Pydantic objects inside business logic.

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

This is not a full application-wide rewrite yet.

For now:

- the order slice is the first repository/adapter proof
- non-order domains may still use their existing JSON validation paths
- heavy dependency injection is intentionally avoided
- stale queue messages and failure handling remain later work

The goal is to prove one clean boundary before expanding it across the rest of the system.

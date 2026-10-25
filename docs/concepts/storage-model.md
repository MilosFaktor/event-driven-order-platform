# Storage Model

Storage is the current business truth of the local app.

Logs explain what happened. Storage records what state the app believes.

## Current Local Storage

The app currently uses JSON files:

```text
data/orders.json
data/idempotency_keys.json
data/processing_queue.json
data/inventory.json
data/invoices.json
data/notifications.json
```

Shared helper:

```text
app/storage/json_storage.py
```

## Main Realization

In-memory storage works only inside one Python process.

When the API and worker run separately, they do not share memory. That is why the project moved to JSON files for local shared state.

## Current Ownership

```text
business service
-> domain repository
-> JSON adapter
-> json_storage
-> data/*.json
```

This boundary is implemented for orders, idempotency keys, the processing
queue, inventory, invoices, and notifications.

## Current Direction

Business behavior works with validated Pydantic objects while adapters own
serialization and validation at the JSON storage edge:

```text
service -> repository -> JSON adapter -> JSON storage
```

The AWS phase can replace JSON adapters with infrastructure-specific adapters
without moving storage mechanics back into services. Candidate backends are:

```text
in-memory
JSON
DynamoDB
```

## Rules For Now

- Do not go back to shared in-memory state for API + worker mode.
- Keep business decisions out of repositories and adapters.
- Replace infrastructure one domain slice at a time during AWS migration.
- Keep JSON storage as a local learning/persistence layer, not production storage.

## AWS Mapping

```text
orders JSON        -> DynamoDB
idempotency JSON   -> DynamoDB
queue JSON         -> SQS
inventory JSON     -> DynamoDB
invoices JSON      -> S3 / DynamoDB metadata
notifications JSON -> SNS / notification tracking
stdout logs        -> CloudWatch
```

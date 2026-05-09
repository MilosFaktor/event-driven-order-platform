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
order_service.py        orders
idempotency_service.py  idempotency keys
queue_service.py        processing queue
inventory_service.py    inventory
invoice_service.py      invoices
notification_service.py notifications
```

## Future Direction

The future direction is:

```text
business logic
-> repository
-> adapter
-> storage backend
```

But this should be added gradually.

First useful slice is probably orders:

```text
Order service -> Order repository -> JSON adapter
```

Later backends could be:

```text
in-memory
JSON
DynamoDB
```

## Rules For Now

- Do not go back to shared in-memory state for API + worker mode.
- Do not rewrite all storage at once.
- Prove repository/adapter on one slice first.
- Keep JSON storage as a local learning/persistence layer, not production storage.

## AWS Mapping

```text
orders JSON       -> DynamoDB
idempotency JSON  -> DynamoDB
queue JSON        -> SQS
inventory JSON    -> DynamoDB
stdout logs       -> CloudWatch
```

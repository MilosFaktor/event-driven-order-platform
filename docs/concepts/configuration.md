# Configuration

Configuration controls runtime behavior without putting flags all over the code.

## Current Setup

Settings live in:

```text
app/core/config.py
```

Current settings:

```text
ENVIRONMENT
LOG_LEVEL
QUEUE_INTERVAL
```

Env files:

```text
.env.example  committed safe defaults
.env.local    private local override
.env.prod     private prod-like override
```

The app defaults to `.env.example`, so a fresh clone can run.

## Rules For Now

- Add config only when the code actually uses it.
- Keep `.env.example` safe and runnable.
- Keep private env files ignored.
- Do not commit secrets.
- Services should use settings through app config, not random `os.getenv()` calls.

## Current Defaults

```text
ENVIRONMENT=local
LOG_LEVEL=INFO
QUEUE_INTERVAL=1
```

For local debugging, `LOG_LEVEL=DEBUG` is useful.

## Future Direction

Retry/DLQ work will probably add:

```text
MAX_RETRIES
RETRY_DELAY_SECONDS
```

Storage abstraction may later add:

```text
STORAGE_BACKEND
```

For AWS, these settings map to Lambda environment variables.

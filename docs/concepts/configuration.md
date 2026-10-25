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
MAX_PROCESSING_ATTEMPTS
RETRY_BASE_DELAY_SECONDS
RETRY_BACKOFF_MULTIPLIER
RETRYABLE_FAILURE_STEPS
```

Env files:

```text
.env.example  committed safe defaults
.env.local    private local override
.env.dev      private development override
.env.prod     private prod-like override
```

The `MODE` environment variable selects the env file. The app defaults to
`.env.example`, so a fresh clone can run.

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
MAX_PROCESSING_ATTEMPTS=4
RETRY_BASE_DELAY_SECONDS=1
RETRY_BACKOFF_MULTIPLIER=2
```

For local debugging, `LOG_LEVEL=DEBUG` is useful.

`RETRYABLE_FAILURE_STEPS` is not present in `.env.example`, so the application
uses its code default:

```text
CAPTURE_PAYMENT
SEND_NOTIFICATION
```

These are the only retryable steps covered by the current behavior tests. The
settings type accepts other valid `OrderFailureStep` values, but the local app
does not claim that those steps are safe to retry.

## Future Direction

Storage abstraction may later add:

```text
STORAGE_BACKEND
```

For AWS, appropriate runtime settings can map to Lambda environment variables.
Retry timing, redelivery, and exhausted-message handling should move to SQS
visibility timeout and redrive policy rather than copying the local blocking
retry loop directly.

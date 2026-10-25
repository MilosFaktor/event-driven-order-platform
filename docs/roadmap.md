# Project Roadmap

The project is developed in phases. Each phase builds on a working result from
the previous phase instead of introducing every cloud concern at once.

## Phase 1 — Local MVP

Status: completed at `v1.0.0`.

Build and verify the order API, worker, pipeline, persistence, retries,
checkpoints, tests, and documentation locally.

## Phase 2 — AWS Serverless MVP

Provision the infrastructure with Terraform and modify the application to run
against AWS services. The local implementation remains available for
development and testing.

| Version | Goal |
| --- | --- |
| `v1.1.0` | Terraform foundation, IAM, test Lambda, deployment packaging, and CloudWatch Logs |
| `v1.2.0` | DynamoDB repositories for orders and idempotency |
| `v1.3.0` | SQS, DLQ, and the AWS queue adapter |
| `v1.4.0` | API Gateway and API Lambda publishing orders to SQS |
| `v1.5.0` | Worker Lambda consuming SQS and executing the existing pipeline |
| `v1.6.0` | AWS-backed inventory, invoices, and notifications |
| `v1.7.0` | Integration tests, alarms, dashboards, security, and reliability hardening |
| `v2.0.0` | Complete and documented AWS serverless deployment |

Dependency order:

```text
Terraform
-> DynamoDB
-> SQS/DLQ
-> API Lambda
-> worker Lambda
-> remaining AWS adapters
-> integration and reliability hardening
```

## Phase 3 — Events and Operations

Add EventBridge domain events, an operations consumer, operational aggregates,
the `/v1/ops/summary` endpoint, metrics, and alarms.

## Phase 4 — Delivery and Infrastructure Hardening

Add reusable Terraform module boundaries, separate development and production
environments, GitHub Actions deployment, production approval, rollback
strategy, and further security hardening.

## Phase 5+ — Advanced Evolution

Consider Step Functions, ECS Fargate, an RDS reporting model, OpenSearch, WAF,
disaster recovery, and advanced scaling only after the core AWS platform is
working and observable.

Overall progression:

```text
local system
-> working AWS system
-> observable event-driven system
-> production-quality delivery
-> optional advanced architecture
```

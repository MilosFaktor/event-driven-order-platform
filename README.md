# Event-Driven Order Processing Platform

This project is a production-style, AWS-first backend system that processes customer orders asynchronously using an event-driven architecture.

The system is designed to simulate how real-world cloud platforms handle:

- asynchronous processing
- failure recovery (DLQ, retries)
- idempotent APIs
- stateful workflows
- observability and operational insight

Orders are accepted through an API, stored in DynamoDB, and processed via SQS-driven workers. The system emits domain events through EventBridge and tracks system performance through an Ops Insights service.

This project evolves in phases from local logic to a fully deployed cloud platform with Terraform and CI/CD.
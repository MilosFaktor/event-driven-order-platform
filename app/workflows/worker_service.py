import time
from dataclasses import dataclass

from app.core.config import Settings
from app.core.logging_config import get_logger
from app.models.order import Order
from app.models.types import WorkerProcessResultOutcome
from app.workflows.protocols import OrderPipelineProtocol, QueueServiceProtocol

logger = get_logger("worker.service")


@dataclass
class WorkerProcessResult:
    outcome: WorkerProcessResultOutcome
    order: Order | None
    message: str


class WorkerService:
    def __init__(
        self,
        settings: Settings,
        queue_service: QueueServiceProtocol,
        order_pipeline_service: OrderPipelineProtocol,
    ):
        self.settings = settings

        self.queue_service = queue_service
        self.order_pipeline_service = order_pipeline_service

    def calculate_retry_delay_seconds(self, attempt: int) -> int:
        return self.settings.retry_base_delay_seconds * (
            self.settings.retry_backoff_multiplier ** (attempt - 1)
        )

    def process_next_order(self) -> WorkerProcessResult:
        order_id = self.queue_service.get_first_queue_item()
        if order_id is None:
            logger.warning("no_order_to_process")
            return WorkerProcessResult(
                WorkerProcessResultOutcome.NO_WORK, None, "No work to do"
            )
        logger.info("order_processing_started order_id=%s", order_id)

        for attempt in range(1, self.settings.max_processing_attempts + 1):
            logger.info(
                "order_processing_attempt_started order_id=%s attempt=%s max_attempts=%s",
                order_id,
                attempt,
                self.settings.max_processing_attempts,
            )

            processed_order = self.order_pipeline_service.process_order(order_id)

            if processed_order is None:
                self.queue_service.dequeue_order()
                logger.warning("stale_queue_message_discarded order_id=%s", order_id)
                return WorkerProcessResult(
                    WorkerProcessResultOutcome.STALE_QUEUE_DISCARDED,
                    None,
                    "Stale queue message discarded",
                )

            if processed_order.status == "COMPLETED":
                self.queue_service.dequeue_order()
                logger.info("order_processing_finished order_id=%s", order_id)
                return WorkerProcessResult(
                    WorkerProcessResultOutcome.SUCCESS,
                    processed_order,
                    "Order processed successfully",
                )

            if processed_order.status == "FAILED":
                if (
                    processed_order.failure_step
                    in self.settings.retryable_failure_steps
                ):
                    if attempt == self.settings.max_processing_attempts:
                        logger.warning(
                            "max_processing_attempts_reached order_id=%s attempt=%s max_attempts=%s",
                            order_id,
                            attempt,
                            self.settings.max_processing_attempts,
                        )
                        self.queue_service.dequeue_order()
                        return WorkerProcessResult(
                            WorkerProcessResultOutcome.FAILURE,
                            processed_order,
                            "Max attempts reached",
                        )

                    delay_seconds = self.calculate_retry_delay_seconds(attempt)
                    logger.info(
                        "order_retry_scheduled order_id=%s attempt=%s retry_delay_seconds=%s",
                        order_id,
                        attempt,
                        delay_seconds,
                    )
                    time.sleep(delay_seconds)
                    continue

                self.queue_service.dequeue_order()
                logger.info(
                    "order_processing_finished_non_retryable_failure order_id=%s failure_step=%s",
                    order_id,
                    processed_order.failure_step,
                )
                return WorkerProcessResult(
                    WorkerProcessResultOutcome.FAILURE,
                    processed_order,
                    "Non-retryable failure occurred",
                )

        raise RuntimeError(
            f"Worker processing ended unexpectedly for order_id={order_id}"
        )

    def has_work(self) -> bool:
        return self.queue_service.not_queue_empty()

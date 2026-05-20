"""
Experimental order pipeline sandbox.

This file is for exploring workflow logic before moving it into app/services.
The production app should not import from this file.
"""

import time

from app.core.config import Settings
from app.core.logging_config import configure_logging_worker, get_logger
from app.services.queue_service import ProcessingQueueService
from app.workflows.order_pipeline_service import OrderPipelineService

configure_logging_worker()
logger = get_logger("sandbox.runtime")


class Sandbox:
    def __init__(
        self,
        settings: Settings | None = None,
        queue_service: ProcessingQueueService | None = None,
        order_pipeline_service: OrderPipelineService | None = None,
    ):
        self.settings = settings or Settings()
        self.queue_service = queue_service or ProcessingQueueService()
        self.order_pipeline_service = order_pipeline_service or OrderPipelineService(
            settings=self.settings
        )

    def calculate_retry_delay_seconds(self, attempt: int) -> int:
        return self.settings.retry_base_delay_seconds * (
            self.settings.retry_backoff_multiplier ** (attempt - 1)
        )

    def exponential_backoff(self):
        for attempt in range(1, self.settings.max_processing_attempts + 1):
            print(f"Attempt {attempt} of {self.settings.max_processing_attempts}")

            failed = True

            if not failed:
                print("Success")
                break

            if attempt == self.settings.max_processing_attempts:
                print("Max attempts reached")  # v0.6.3 - DLQ
                break

            delay_seconds = self.calculate_retry_delay_seconds(attempt)
            print(f"Retrying in {delay_seconds} seconds")
            time.sleep(delay_seconds)

    def process_next_order(self):
        order_id = self.queue_service.get_first_queue_item()
        if order_id is None:
            logger.warning("no_order_to_process")
            return None
        logger.info("order_processing_started order_id=%s", order_id)

        for attempt in range(1, self.settings.max_processing_attempts + 1):
            print(f"Attempt {attempt} of {self.settings.max_processing_attempts}")

            processed_order = self.order_pipeline_service.process_order(order_id)

            if processed_order is None:
                self.queue_service.dequeue_order()
                logger.warning("stale_queue_message_discarded order_id=%s", order_id)
                return "stale_queue_discarded"

            if processed_order.status == "COMPLETED":
                self.queue_service.dequeue_order()
                logger.info("order_processing_finished order_id=%s", order_id)
                return processed_order

            if processed_order.status == "FAILED":
                if (
                    processed_order.failure_step
                    in self.settings.retryable_failure_steps
                ):
                    if attempt == self.settings.max_processing_attempts:
                        print("Max attempts reached")  # v0.6.3 - DLQ
                        self.queue_service.dequeue_order()
                        return processed_order

                    delay_seconds = self.calculate_retry_delay_seconds(attempt)
                    print(f"Retrying in {delay_seconds} seconds")
                    time.sleep(delay_seconds)
                    continue

                self.queue_service.dequeue_order()
                logger.info(
                    "order_processing_finished_non_retryable_failure order_id=%s failure_step=%s",
                    order_id,
                    processed_order.failure_step,
                )
                return processed_order


sandbox = Sandbox()
print(sandbox.process_next_order())

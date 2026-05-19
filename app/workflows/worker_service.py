from app.core.logging_config import get_logger
from app.services.queue_service import ProcessingQueueService
from app.workflows.order_pipeline_service import OrderPipelineService

logger = get_logger("worker.service")


class WorkerService:
    def __init__(
        self,
        queue_service: ProcessingQueueService | None = None,
        order_pipeline_service: OrderPipelineService | None = None,
    ):
        self.queue_service = queue_service or ProcessingQueueService()
        self.order_pipeline_service = order_pipeline_service or OrderPipelineService()

    def process_next_order(self):
        order_id = self.queue_service.get_first_queue_item()
        if order_id is None:
            logger.warning("no_order_to_process")
            return None
        logger.info("order_processing_started order_id=%s", order_id)
        processed_order = self.order_pipeline_service.process_order(order_id)

        if processed_order is None:
            self.queue_service.dequeue_order()  # dequeue after finding stale queue
            logger.warning("stale_queue_message_discarded order_id=%s", order_id)
            return "stale_queue_discarded"

        self.queue_service.dequeue_order()  # dequeue after successful processing
        logger.info("order_processing_finished order_id=%s", order_id)

        return processed_order

    def has_work(self) -> bool:
        return self.queue_service.not_queue_empty()

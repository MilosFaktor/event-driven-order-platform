from app.core.logging_config import get_logger
from app.repositories.idempotency_repository import IdempotencyKeysRepository

logger = get_logger("idempotency.service")


class IdempotencyKeysService:
    def __init__(self, repo: IdempotencyKeysRepository | None = None):
        if repo is None:
            self.repo = IdempotencyKeysRepository()
        else:
            self.repo = repo

    def get_order_id_by_idempotency_key(self, idempotency_key):
        idempotency_keys = self.repo.list_idempotency_keys()
        order_id = idempotency_keys.root.get(idempotency_key)

        if order_id is None:
            logger.debug("idempotency_key_not_found")
        else:
            logger.info("idempotency_key_matched order_id=%s", order_id)

        return order_id

    def list_idempotency_keys(self):
        return self.repo.list_idempotency_keys()

    def save_idempotency_key(self, idempotency_key, order_id):
        idempotency_keys = self.repo.list_idempotency_keys()
        idempotency_keys.root[idempotency_key] = order_id
        self.repo.save_idempotency_keys(idempotency_keys)

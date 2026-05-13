from app.adapters.json_idempotency_adapter import IdempotencyKeysAdapter
from app.core.logging_config import get_logger
from app.models.idempotency_keys import IdempotencyKeys

logger = get_logger("idempotency_keys.repo")


class IdempotencyKeysRepository:
    def __init__(self, adapter: IdempotencyKeysAdapter | None = None):
        if adapter is None:
            self.adapter = IdempotencyKeysAdapter()
        else:
            self.adapter = adapter

    def list_idempotency_keys(self) -> IdempotencyKeys:
        idempotency_keys = self.adapter.load_idempotency_keys()
        logger.debug("idempotency_keys_loaded count=%s", len(idempotency_keys.root))

        return idempotency_keys

    def save_idempotency_keys(self, idempotency_keys: IdempotencyKeys) -> None:
        self.adapter.save_idempotency_keys(idempotency_keys)
        logger.debug("idempotency_keys_saved count=%s", len(idempotency_keys.root))

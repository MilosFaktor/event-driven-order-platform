from app.models.idempotency_keys import IdempotencyKeys
from app.storage import json_storage

IDEMPOTENCY_KEYS_PATH = json_storage.STORAGE_PATHS["idempotency_keys"]


class IdempotencyKeysAdapter:
    def __init__(self, idempotency_keys_path: str = IDEMPOTENCY_KEYS_PATH):
        self.idempotency_keys_path = idempotency_keys_path

    def load_idempotency_keys(self) -> IdempotencyKeys:
        raw_idempotency_keys = json_storage.load_json(self.idempotency_keys_path)
        return IdempotencyKeys.model_validate(raw_idempotency_keys)

    def save_idempotency_keys(self, idempotency_keys: IdempotencyKeys) -> None:
        json_storage.save_json(
            self.idempotency_keys_path, idempotency_keys.model_dump()
        )

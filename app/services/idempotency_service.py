from app.core.logging_config import get_logger
from app.storage import json_storage

IDEMPOTENCY_KEYS_PATH = json_storage.STORAGE_PATHS["idempotency_keys"]

logger = get_logger("idempotency.service")


def get_idempotency_keys():
    return json_storage.load_json(IDEMPOTENCY_KEYS_PATH)


def get_order_id_by_idempotency_key(idempotency_key):
    idempotency_keys = get_idempotency_keys()
    order_id = idempotency_keys.get(idempotency_key)
    if order_id is None:
        logger.debug("idempotency_key_not_found")
    else:
        logger.info("idempotency_key_matched order_id=%s", order_id)
    return order_id


def store_idempotency_key(idempotency_key, order_id):
    idempotency_keys = get_idempotency_keys()
    idempotency_keys[idempotency_key] = order_id
    json_storage.save_json(IDEMPOTENCY_KEYS_PATH, idempotency_keys)
    logger.info("idempotency_key_stored order_id=%s", order_id)

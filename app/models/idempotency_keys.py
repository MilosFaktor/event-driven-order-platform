from pydantic import RootModel


class IdempotencyKeys(RootModel[dict[str, str]]):
    pass

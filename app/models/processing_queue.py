from pydantic import RootModel


class ProcessingQueue(RootModel[list[str]]):
    pass

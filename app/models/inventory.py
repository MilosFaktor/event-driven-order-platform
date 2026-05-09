from pydantic import BaseModel, ConfigDict, Field, RootModel


class InventoryItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    name: str
    price: int = Field(ge=0)
    available_stock: int = Field(ge=0)
    reserved_stock: int = Field(ge=0)
    sold_stock: int = Field(ge=0)


class Inventory(RootModel[dict[str, InventoryItem]]):
    pass

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class SnekBase(SQLModel):
    class Config:
        allow_population_by_field_name = True

    species: str = Field(
        description="Name of the Snek species in English.",
        min_length=3,
        max_length=256,
        schema_extra={
            "examples": ["Indian Python", "King Cobra"],
        },
    )
    length: float = Field(
        description="Current length of the Snek in meters.",
        gt=0,  # sneks usually don't have a negative length
        le=20,  # longest snek ever recorded was 10m long
        schema_extra={
            "examples": [3, 3.6],
        },
    )
    venomous: bool = Field(
        description="Whether the Snek species is venomous.",
        schema_extra={
            "examples": [False, True],
        },
    )


class Snek(SnekBase, table=True):
    id_: int | None = Field(
        default=None,
        primary_key=True,
        alias="id",
    )


class SnekCreate(SnekBase):
    pass


class SnekRead(SnekBase):
    id_: int = Field(
        description="Internal numeric ID of the Snek.",
        alias="id",
    )


class OperationResult(BaseModel):
    result: str

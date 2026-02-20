from typing import Literal
from pydantic import BaseModel, field_validator, model_validator


class ModuleSpec(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    description: str
    required: bool


class BuildSpec(BaseModel):
    model_config = {"extra": "forbid"}

    project_name: str
    language: Literal["python"]
    modules: list[ModuleSpec]
    constraints: list[str]
    test_required: bool
    max_files: int

    @field_validator("max_files")
    @classmethod
    def max_files_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_files must be greater than 0")
        return v

    @model_validator(mode="after")
    def at_least_one_module(self) -> "BuildSpec":
        if not self.modules:
            raise ValueError("at least one module is required")
        return self

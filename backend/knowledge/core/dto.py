from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DTO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True,
                              from_attributes=True, extra="forbid")

    def public(self) -> dict:
        return self.model_dump(mode="json", by_alias=True)

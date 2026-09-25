from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# SQLAlchemy INET columns return ipaddress objects; the public contract is a string.
StrIp = Annotated[str, BeforeValidator(lambda v: str(v) if v is not None else v)]

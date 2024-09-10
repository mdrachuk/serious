import json
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel

from serious import DictModel


class UserType(Enum):
    person = "person"
    bot = "bot"


class User(BaseModel):
    __tablename__ = "users"

    id: int
    name: str
    type: UserType


@dataclass
class UserContainer:
    user: User


def test_pydantic_model_is_serialized():
    model = DictModel(UserContainer)
    raw_user = json.dumps({"id": 1, "name": "John", "type": "person"}, separators=(",", ":"))
    container = model.load({"user": raw_user})
    assert container.user.type is UserType.person
    assert container.user.name == "John"

    assert model.dump(container) == {
        "user": raw_user
    }

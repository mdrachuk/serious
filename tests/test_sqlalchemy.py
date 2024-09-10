from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, declared_attr

from serious import DictModel

Base = declarative_base()


class UserType(Enum):
    person = "person"
    bot = "bot"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    type: Mapped[UserType]

    @declared_attr
    def created_at(cls):
        return Column(DateTime, nullable=False)


@dataclass
class UserContainer:
    user: User


class GroupType(Enum):
    private = "private"
    public = "public"


class Group(Base):
    __tablename__ = "groups"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(255))
    type: GroupType = Column(sqlalchemy.Enum(GroupType))


@dataclass
class GroupContainer:
    group: Group


def test_sqlalchemy_mapped_model_is_serialized():
    model = DictModel(UserContainer)
    container = model.load({"user": {"id": 1, "name": "John", "type": "person", "created_at": "2021-01-01T00:00:00"}})
    assert container.user.type is UserType.person
    assert container.user.name == "John"
    assert container.user.created_at == datetime.fromisoformat("2021-01-01T00:00:00")

    assert model.dump(container) == {
        "user": {"id": 1, "name": "John", "type": "person", "created_at": "2021-01-01T00:00:00"}
    }


def test_sqlalchemy_column_model_is_serializable():
    model = DictModel(GroupContainer)
    container = model.load({"group": {"id": 1, "name": "First", "type": "private"}})
    assert container.group.type is GroupType.private
    assert container.group.name == "First"

    assert model.dump(container) == {
        "group": {"id": 1, "name": "First", "type": "private"}
    }

from sqlmodel import SQLModel
from whenever import Instant, PlainDateTime

import activemodel
from activemodel import BaseModel
from activemodel.mixins.typeid import TypeIDMixin
from activemodel.session_manager import get_engine

# Although this looks like it's an absolute path, it is translated into a relative path based on the source location of this file
activemodel.init("sqlite:///database.db")


class User(
    BaseModel,
    # you can use a different pk type, but why would you?
    # put this mixin last otherwise `id` will not be the first column in the DB
    TypeIDMixin("user"),
    # wire this model into the DB, without this alembic will not generate a migration
    table=True,
):
    # PlainDateTime matches SQLite behavior: no timezone support
    booked_date: PlainDateTime


# This magic command enables you to avoid the need to run or manage migrations and just magically creates all the tables in the local database
SQLModel.metadata.create_all(get_engine())

now_in_sys_time = Instant.now().to_system_tz().to_plain()

user = User(booked_date=now_in_sys_time).save()
fresh_user = User.one(user.id)

assert fresh_user.booked_date == now_in_sys_time

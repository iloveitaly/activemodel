#!/usr/bin/env -S uv tool run ipython -i

import sqlalchemy as sa
import sqlmodel as sm
from activemodel.session_manager import get_session
from tests.models import *

from sqlmodel import SQLModel
from activemodel import get_engine
import activemodel
from tests.utils import database_url

activemodel.init(database_url())

SQLModel.metadata.create_all(get_engine())

session = get_session()

"""
compile_sql(sm.select(AnotherExample).with_only_columns(sm.func.count()))
"""
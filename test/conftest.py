import activemodel

from .utils import database_url

activemodel.init(database_url())

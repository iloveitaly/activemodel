import inspect
import pkgutil
import sys
from types import ModuleType

from sqlalchemy import text
from sqlmodel import SQLModel
from sqlmodel.sql.expression import SelectOfScalar

from .logger import logger
from .session_manager import get_engine, get_session


def compile_sql(target: SelectOfScalar):
    "convert a query into SQL, helpful for debugging"
    dialect = get_engine().dialect
    # TODO I wonder if we could store the dialect to avoid getting an engine reference
    compiled = target.compile(dialect=dialect, compile_kwargs={"literal_binds": True})
    return str(compiled)


# TODO document further, lots of risks here
def raw_sql_exec(raw_query: str):
    with get_session() as session:
        session.execute(text(raw_query))


def find_all_sqlmodels(module: ModuleType):
    """Import all model classes from module and submodules into current namespace."""

    logger.debug(f"Starting model import from module: {module.__name__}")
    model_classes = {}

    # Walk through all submodules
    for loader, module_name, is_pkg in pkgutil.walk_packages(module.__path__):
        full_name = f"{module.__name__}.{module_name}"
        logger.debug(f"Importing submodule: {full_name}")

        # Check if module is already imported
        if full_name in sys.modules:
            submodule = sys.modules[full_name]
        else:
            logger.warning(
                f"Module not found in sys.modules, not importing: {full_name}"
            )
            continue

        # Get all classes from module
        for name, obj in inspect.getmembers(submodule):
            if inspect.isclass(obj) and issubclass(obj, SQLModel) and obj != SQLModel:
                logger.debug(f"Found model class: {name}")
                model_classes[name] = obj

    logger.debug(f"Completed model import. Found {len(model_classes)} models")
    return model_classes


def hash_function_code(func):
    "get sha of a function to easily assert that it hasn't changed"

    import hashlib
    import inspect

    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()

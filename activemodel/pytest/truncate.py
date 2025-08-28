import os
from typing import Iterable

import pytest
from sqlmodel import SQLModel

from ..logger import logger
from ..session_manager import get_engine
from pytest import Config
import typing as t

T = t.TypeVar("T")


def _normalize_to_list_of_strings(str_or_list: list[str] | str) -> list[str]:
    if isinstance(str_or_list, list):
        return str_or_list

    raw_list = str_or_list.split(",")
    return [entry.strip() for entry in raw_list if entry and entry.strip()]


def _get_pytest_option(
    config: Config, key: str, *, cast: t.Callable[[t.Any], T] | None = str
) -> T | None:
    if not config:
        return None

    try:
        val = config.getoption(key)
    except ValueError:
        val = None

    if val is None:
        val = config.getini(key)

    if val is not None:
        if cast:
            return cast(val)

        return val

    return None


def _normalize_preserve_tables(raw: Iterable[str]) -> list[str]:
    """Normalize user supplied table list: strip, dedupe (order not preserved).

    Returns a sorted list (case-insensitive sort while preserving original casing
    for readability in logs).
    """

    cleaned = {name.strip() for name in raw if name and name.strip()}
    # deterministic order: casefold sort
    return sorted(cleaned, key=lambda s: s.casefold())


def _get_excluded_tables(
    pytest_config: Config | None, preserve_tables: list[str] | None
) -> list[str]:
    """Resolve list of tables to exclude (i.e. *preserve* / NOT truncate).

    Precedence (lowest -> highest):
        1. pytest ini option ``activemodel_preserve_tables`` (if available)
        2. Environment variable ``ACTIVEMODEL_PRESERVE_TABLES`` (comma separated)
        3. Function argument ``preserve_tables``

            Behavior:
                    * If user supplies nothing via any channel, defaults to ["alembic_version"].
                    * Case-insensitive matching during truncation; returned list is normalized
                        (deduped, sorted) for deterministic logging.
                    * Emits a warning only when the ini option is *explicitly* specified but empty after normalization.
    """

    # 1. pytest ini option (registered as type="linelist" -> typically list[str])
    ini_tables = (
        _get_pytest_option(
            pytest_config,
            "activemodel_preserve_tables",
            cast=_normalize_to_list_of_strings,
        )
        or []
    )

    # 2. environment variable
    env_var = os.getenv("ACTIVEMODEL_PRESERVE_TABLES", "")
    env_tables = _normalize_to_list_of_strings(env_var)

    # 3. function argument
    arg_tables = preserve_tables or []

    # Consider customization only if any non-empty source provided values OR the function arg explicitly passed
    combined_raw = [*ini_tables, *env_tables, *arg_tables]

    # if no user customization, force alembic_version
    if not combined_raw:
        return ["alembic_version"]

    normalized = _normalize_preserve_tables(combined_raw)
    logger.debug(f"excluded tables for truncation: {normalized}")

    return normalized


def database_reset_truncate(
    preserve_tables: list[str] | None = None, pytest_config: Config | None = None
):
    """
    Transaction is most likely the better way to go, but there are some scenarios where the session override
    logic does not work properly and you need to truncate tables back to their original state.

    Here's how to do this once at the start of the test:

    >>> from activemodel.pytest import database_reset_truncation
    >>> def pytest_configure(config):
    >>> 	database_reset_truncation()

    Or, if you want to use this as a fixture:

    >>> pytest.fixture(scope="function")(database_reset_truncation)
    >>> def test_the_thing(database_reset_truncation)

    This approach has a couple of problems:

    * You can't run multiple tests in parallel without separate databases
    * If you have important seed data and want to truncate those tables, the seed data will be lost
    """

    logger.info("truncating database")

    # Determine excluded (preserved) tables and build case-insensitive lookup set
    exception_tables = _get_excluded_tables(pytest_config, preserve_tables)
    exception_lookup = {t.lower() for t in exception_tables}

    assert SQLModel.metadata.sorted_tables, (
        "No model metadata. Ensure model metadata is imported before running truncate_db"
    )

    with get_engine().connect() as connection:
        for table in reversed(SQLModel.metadata.sorted_tables):
            transaction = connection.begin()

            if table.name.lower() not in exception_lookup:
                logger.debug(f"truncating table={table.name}")
                connection.execute(table.delete())

            transaction.commit()

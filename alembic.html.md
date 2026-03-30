# Integrating Alembic

`alembic init` will not work out of the box. You need to mutate a handful of files:

* To import all of your models you want in your DB. [Here’s my recommended way to do this.](https://github.com/iloveitaly/python-starter-template/blob/master/app/models/__init__.py)
* Use your DB URL from the ENV
* Target sqlalchemy metadata to the sqlmodel-generated metadata
* Most likely you’ll want to add [alembic-postgresql-enum](https://pypi.org/project/alembic-postgresql-enum/) so migrations work properly

[Take a look at these scripts for an example of how to fully integrate Alembic into your development workflow.](https://github.com/iloveitaly/python-starter-template/blob/0af2c7e95217e34bde7357cc95be048900000e48/Justfile#L618-L712)

Here’s a diff from the bare `alembic init` from version `1.14.1`.

```diff
diff --git i/tests/migrations/alembic.ini w/tests/migrations/alembic.ini
index 0d07420..a63631c 100644
--- i/tests/migrations/alembic.ini
+++ w/tests/migrations/alembic.ini
@@ -3,13 +3,14 @@
 [alembic]
 # path to migration scripts
 # Use forward slashes (/) also on windows to provide an os agnostic path
-script_location = .
+script_location = migrations

 # template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
 # Uncomment the line below if you want the files to be prepended with date and time
 # see https://alembic.sqlalchemy.org/en/latest/tutorial.html#editing-the-ini-file
 # for all available tokens
 # file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s
+file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(rev)s_%%(slug)s

 # sys.path path, will be prepended to sys.path if present.
 # defaults to the current working directory.
diff --git i/tests/migrations/env.py w/tests/migrations/env.py
index 36112a3..a1e15c2 100644
--- i/tests/migrations/env.py
+++ w/tests/migrations/env.py
@@ -1,3 +1,6 @@
+# fmt: off
+# isort: off
+
 from logging.config import fileConfig

 from sqlalchemy import engine_from_config
@@ -14,11 +17,17 @@ config = context.config
 if config.config_file_name is not None:
     fileConfig(config.config_file_name)

+from sqlmodel import SQLModel
+from tests.models import *
+from tests.utils import database_url
+
+config.set_main_option("sqlalchemy.url", database_url())
+
 # add your model's MetaData object here
 # for 'autogenerate' support
 # from myapp import mymodel
 # target_metadata = mymodel.Base.metadata
-target_metadata = None
+target_metadata = SQLModel.metadata

 # other values from the config, defined by the needs of env.py,
 # can be acquired:
diff --git i/tests/migrations/script.py.mako w/tests/migrations/script.py.mako
index fbc4b07..9dc78bb 100644
--- i/tests/migrations/script.py.mako
+++ w/tests/migrations/script.py.mako
@@ -9,6 +9,8 @@ from typing import Sequence, Union

 from alembic import op
 import sqlalchemy as sa
+import sqlmodel
+import activemodel
 ${imports if imports else ""}

 # revision identifiers, used by Alembic.
```

Here are some useful resources around Alembic + SQLModel:

* https://github.com/fastapi/sqlmodel/issues/85
* https://testdriven.io/blog/fastapi-sqlmodel/

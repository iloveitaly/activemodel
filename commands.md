## Standalone Python Scripts

Use this header:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
```

- Specify dependencies via the `dependencies` variable in the above comment
- Do not install packages with pip or any other package manager, assume packages will be installed when needed using `uv run --script`.
- Use `click` for CLI interfaces
- When listing constants at the top of the file, include a newline between entries and (for non-obvious constants) document each constant with a comment:

```python
# matches full lowercase git shas (short or full)
SHA_REGEX = re.compile(r"^[0-9a-f]{7,40}$")

# matches any char not allowed in dns labels
SAFE_CHARS_REGEX = re.compile(r"[^a-z0-9-]")

DEFAULT_ENVIRONMENT_NAME = "production"
DEFAULT_SERVICE_NAME = "Postgres"
```

### CLI Output and Logging

- Use `structlog_config` for logging. Read the usage guide: @https://github.com/iloveitaly/structlog-config/
- Use logging for operational/debugging info that goes to structured logs.
- Use CLI output for user-facing messages the user needs to see during normal execution (status updates, warnings, errors). Color these messages.

## Write Or Update Readme

Write or update the @README.md:

* First, think hard and investigate the source code in the repository to understand what it does
* If the readme already exists, do not reword sections which feel complete or whose functionality has not changed.
  * However, if specific rules below conflict with what is written, follow the rules below
* Be concise, do not use too many adjectives
* The title should be a short description of the project, not just the project name
* Don't try to be exciting or creative
  * No story telling
  * Do not be overly salesly.
  * Omit phrases like "The tool is designed to be smart" which don't say anything useful
* No emojis
* Assume `uv` and omit pip examples
* Include a single line at the end `## [MIT License](LICENSE.md)` (above any template attribution)
* When writing the overview and `#` header, be sure to:
  * Think of what keywords another developer might search for.
  * Include the primary goal of the project or primary problem solved in a short paragraph.
    * If you aren't sure what the primary goal of the project is, ask.
    * For the title, don't include just the name of the package. Instead make it a short description of the project. Just a handful of words, such as 'Manage Python Project
      Dependencies'
* After a general overview, include the following sections: Installation, Usage, Features.
  * When writing out a list of features, use a bullet list.
  * Do not include "internal" features like `  * **Python 3.13+ with modern type parameter syntax**`
* Do not include every usage example varaint for a CLI or library. The goal is to give an overview so the user can figure out the rest on their own.
* Do not remove badges or link to upstream template repo

Here's the writing style you should use:

> Conversational and personal, often in first-person with enthusiastic, reflective tone on tech, startups, and health topics. Logical structure: hooks, breakdowns via subsections/lists, and practical steps. Vocabulary mixes everyday terms with technical jargon (e.g., tmux, Caddy, REPL). Short-to-medium sentences for clarity; semi-formal with casual asides and anecdotes

### Update `pyproject.toml` metadata

Update the `pyproject.toml` keywords (maximum of 4) and description based on the contents of this repo. Do not use `.` in a keyword.

## Upgrade SQLModel

Upgrade the pinned sqlmodel dependency to the latest PyPI release and make sure everything still works.

Context:

* sqlmodel is pinned exactly in `pyproject.toml` (e.g. `sqlmodel==X.Y.Z`)
* `activemodel/patches/` monkey-patches private `sqlmodel.main` helpers:
  * `get_column_from_field_patch.py` — field description → column comment
  * `get_sqlalchemy_type_patch.py` — whenever datetime types
* Each patch asserts `hash_function_code(...)` against the upstream function source. If the hash fails, the upstream body changed and the patch must be re-verified.
* Patches mark our edits with `# <Change>` / `# </Change>` comments. Keep those changes; rebase them onto the new upstream body.

Steps:

1. Read the current pin from `pyproject.toml` and the latest version from PyPI. If already latest, stop.
2. Bump with `uv add "sqlmodel==<latest>"` so `uv.lock` updates.
3. For each patched function:
   1. Diff the function between the old and new sqlmodel tags (`fastapi/sqlmodel` on GitHub, `sqlmodel/main.py`).
   2. If the body is identical, only refresh the GitHub source link in the patch comment if needed.
   3. If it changed, copy the new upstream body into the patch, re-apply our `# <Change>` blocks, and update the expected hash to `hash_function_code` of the *new* upstream function (the assert runs before the monkey-patch assignment).
4. Start deps if needed (`just docker_up`), then run `just test` and `just lint`.
5. Fix any failures caused by the upgrade. Do not commit.

Report: old → new version, what changed in each patched function, and test/lint results.


# activemodel.jsonb_snapshot

Serialize-and-compare snapshot tracking for Pydantic JSON fields.

After each ORM load/refresh, each Pydantic JSON field is serialized to a canonical
JSON string and stored as a snapshot. Before commit, the current value is re-serialized
and compared; if the strings differ, flag_modified is called so SQLAlchemy includes
the column in the UPDATE.

This mirrors how Rails’ ActiveRecord handles JSON column dirty-tracking: compare the
serialized form of the current value against the serialized form of the original, rather
than intercepting every mutation with proxy objects.

## Functions

| [`snapshot_pydantic_fields`](#activemodel.jsonb_snapshot.snapshot_pydantic_fields)(→ None)               | Store a serialized snapshot of each Pydantic JSON field on the instance.          |
|----------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| [`detect_json_mutations`](#activemodel.jsonb_snapshot.detect_json_mutations)(→ list[str])                | Compare current field values against snapshots, flagging any that changed.        |
| [`register_before_commit_listener`](#activemodel.jsonb_snapshot.register_before_commit_listener)(→ None) | Register a session-level before_commit handler to detect in-place JSON mutations. |

## Module Contents

### activemodel.jsonb_snapshot.snapshot_pydantic_fields(instance, jsonb_field_names: [set](https://docs.python.org/3/library/stdtypes.html#set)[[str](https://docs.python.org/3/library/stdtypes.html#str)] | [None](https://docs.python.org/3/library/constants.html#None) = None) → [None](https://docs.python.org/3/library/constants.html#None)

Store a serialized snapshot of each Pydantic JSON field on the instance.

Called after rehydration so the snapshot reflects the committed database state.
When jsonb_field_names is provided (partial refresh), only those fields are
re-snapshotted; existing snapshots for other fields are preserved.

### activemodel.jsonb_snapshot.detect_json_mutations(instance) → [list](https://docs.python.org/3/library/stdtypes.html#list)[[str](https://docs.python.org/3/library/stdtypes.html#str)]

Compare current field values against snapshots, flagging any that changed.

Returns a list of field names that were mutated since the last snapshot.
Side effect: calls flag_modified on the SQLAlchemy instance for each changed field.

### activemodel.jsonb_snapshot.register_before_commit_listener() → [None](https://docs.python.org/3/library/constants.html#None)

Register a session-level before_commit handler to detect in-place JSON mutations.

Uses before_commit (not before_flush) because SQLAlchemy skips the flush entirely
when it sees no pending changes – meaning before_flush never fires for in-place
mutations that haven’t been explicitly flagged. before_commit fires unconditionally,
giving us the chance to call flag_modified before the flush decision is made.

Safe to call multiple times – the listener is only registered once.

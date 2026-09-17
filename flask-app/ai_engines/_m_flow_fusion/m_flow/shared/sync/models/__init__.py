# ---------------------------------------------------------------------------
# m_flow.shared.sync.models — ORM + Pydantic models for sync lifecycle
# ---------------------------------------------------------------------------
# A sync operation progresses through a deterministic state machine:
#
#   PENDING  →  RUNNING  →  COMPLETED
#                  ↓
#               FAILED
#
# Both ``SyncOperation`` and its companion enum ``SyncStatus`` live in
# a single module to keep the import graph shallow.
# ---------------------------------------------------------------------------

import importlib as _il

_op_mod = _il.import_module(".SyncOperation", __name__)

SyncOperation = _op_mod.SyncOperation
SyncStatus = _op_mod.SyncStatus

del _il, _op_mod

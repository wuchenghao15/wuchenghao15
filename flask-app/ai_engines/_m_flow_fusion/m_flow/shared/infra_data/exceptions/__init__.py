# ---------------------------------------------------------------------------
# m_flow.shared.infra_data.exceptions
# ---------------------------------------------------------------------------
# Error hierarchy for the data-infrastructure layer.  Every exception
# defined here inherits ``BadInputError`` so HTTP handlers can
# translate them to proper 4xx responses without extra mapping logic.
# ---------------------------------------------------------------------------

import importlib as _il

_exc_mod = _il.import_module(".exceptions", __name__)
KeywordExtractionError = _exc_mod.KeywordExtractionError

del _il, _exc_mod

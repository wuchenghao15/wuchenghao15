# ---------------------------------------------------------------------------
# m_flow.shared.loaders.core — built-in, zero-extra-dependency loaders
# ---------------------------------------------------------------------------
# These implementations rely only on the Python standard library plus
# packages already pulled in by the core ``m_flow`` install.
#
# Loader discovery is handled lazily: the ``LoaderEngine`` imports this
# package once during its first ``load()`` call, not at process startup.
# ---------------------------------------------------------------------------

import importlib as _il

# Lazy re-exports — avoids top-level I/O at import time.
TextLoader = _il.import_module(".text_loader", __name__).TextLoader
AudioLoader = _il.import_module(".audio_loader", __name__).AudioLoader
ImageLoader = _il.import_module(".image_loader", __name__).ImageLoader
CsvLoader = _il.import_module(".csv_loader", __name__).CsvLoader

del _il  # keep module namespace clean

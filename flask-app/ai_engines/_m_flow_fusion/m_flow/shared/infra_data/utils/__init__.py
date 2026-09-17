# m_flow.shared.infra_data.utils
# Lightweight helpers consumed by the data-infrastructure layer.
#
# These routines are intentionally kept dependency-free so they can be
# imported early during pipeline bootstrap without triggering heavy
# third-party loads.

_UTILS_SENTINEL = True

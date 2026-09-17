"""
Debug and inspection utilities (P6-4).

This package contains command-line tools for debugging M-flow pipelines
and inspecting internal data structures.

Available Tools
---------------

trace_cli
    Inspect and visualize trace files generated during pipeline execution.

    Run with: ``python -m m_flow.debug.trace_cli --trace_id <id>``

procedure_cli
    Examine procedure structures and their execution history.

    Run with: ``python -m m_flow.debug.procedure_cli --procedure_id <id>``

Note: These tools are intended for development and debugging purposes only.
"""

__all__: list[str] = []

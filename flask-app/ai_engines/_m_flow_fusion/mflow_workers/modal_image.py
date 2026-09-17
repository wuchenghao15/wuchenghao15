"""
Modal容器镜像配置
"""

from __future__ import annotations

import pathlib

from modal import Image

_DOCKERFILE = pathlib.Path(__file__).parent / "Dockerfile"

image = Image.from_dockerfile(
    path=_DOCKERFILE.resolve(),
    force_build=False,
).add_local_python_source("m_flow", "entrypoint")

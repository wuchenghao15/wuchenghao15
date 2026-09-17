"""
分布式处理工具函数
"""

from __future__ import annotations

import os
from functools import wraps
from typing import Callable

_DIST_ENV = "MFLOW_DISTRIBUTED"


def override_distributed(distributed_impl: Callable):
    """
    分布式执行装饰器

    根据环境变量或参数决定使用分布式还是本地实现
    """

    def decorator(local_impl: Callable):
        @wraps(local_impl)
        async def wrapper(self, *args, distributed: bool | None = None, **kwargs):
            use_distributed = os.getenv(_DIST_ENV, "false").lower() == "true" if distributed is None else distributed

            if use_distributed:
                return await distributed_impl(*args, **kwargs)
            return await local_impl(self, *args, **kwargs)

        return wrapper

    return decorator

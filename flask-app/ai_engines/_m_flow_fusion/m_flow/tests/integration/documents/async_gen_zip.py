"""
异步生成器zip工具
"""

from __future__ import annotations

from typing import AsyncIterator, Iterable, Tuple, TypeVar

T1 = TypeVar("T1")
T2 = TypeVar("T2")


async def async_gen_zip(sync_iter: Iterable[T1], async_iter: AsyncIterator[T2]) -> AsyncIterator[Tuple[T1, T2]]:
    """将同步迭代器与异步迭代器配对"""
    sync_it = iter(sync_iter)
    async_it = async_iter.__aiter__()

    while True:
        try:
            v1 = next(sync_it)
            v2 = await async_it.__anext__()
            yield v1, v2
        except (StopIteration, StopAsyncIteration):
            return

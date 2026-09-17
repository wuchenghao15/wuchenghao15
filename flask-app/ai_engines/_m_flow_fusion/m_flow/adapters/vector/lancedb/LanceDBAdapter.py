"""
LanceDB vector database adapter.

Provides implementation for vector storage, retrieval and search functionality.
"""

from __future__ import annotations

import asyncio
import re
from os import path
from typing import (
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import lancedb
from lancedb.pydantic import LanceModel, Vector
from pydantic import BaseModel

from m_flow.adapters.exceptions import MissingQueryParameterError
from m_flow.adapters.vector.exceptions import CollectionNotFoundError
from m_flow.core import MemoryNode
from m_flow.core.utils import parse_id
from m_flow.shared.files.storage import get_file_storage
from m_flow.storage.utils_mod.utils import copy_model, get_own_properties

from ..embeddings.EmbeddingEngine import EmbeddingEngine
from ..models.VectorSearchHit import VectorSearchHit
from ..utils import normalize_distances
from ..vector_db_interface import VectorProvider

# Type variable definitions
_IdT = TypeVar("_IdT")
_PayloadT = TypeVar("_PayloadT")

# Whitelist of allowed filter fields and values
# None value means any value is allowed (for dynamic fields like dataset_id)
_FILTER_WHITELIST: dict[str, list[str] | None] = {
    "memory_type": ["atomic", "episodic"],
    "dataset_id": None,  # 允许任意 UUID 值
}


def _build_stripped_schema(
    src_model: type[BaseModel],
    base_cls: type,
) -> type[BaseModel]:
    """
    构建精简的schema，排除关联模型字段
    """
    excluded_fields = ["metadata"]

    for fname, fcfg in src_model.model_fields.items():
        annotation = fcfg.annotation

        # 检查直接的model_fields属性
        if hasattr(fcfg, "model_fields") or hasattr(annotation, "model_fields"):
            excluded_fields.append(fname)
            continue

        origin = get_origin(annotation)

        # 处理Union或list类型
        if origin is Union or origin is list:
            args = get_args(annotation)
            if any(hasattr(a, "model_fields") for a in args):
                excluded_fields.append(fname)
            elif args and any(get_args(a) is base_cls for a in args):
                excluded_fields.append(fname)
            elif args and any(sub is base_cls for sub in get_args(args[0]) if get_args(args[0])):
                excluded_fields.append(fname)

        # 处理Optional类型
        elif origin is Optional:
            inner = get_args(annotation)
            if hasattr(inner, "model_fields"):
                excluded_fields.append(fname)

    return copy_model(
        src_model,
        include_fields={"id": (str, ...)},
        exclude_fields=excluded_fields,
    )


def _check_filter_security(filter_expr: str) -> None:
    """
    验证过滤表达式的安全性，防止注入攻击
    """
    if not filter_expr:
        return

    # 严格匹配 payload.field = 'value' 格式
    # 值部分使用 [\w-]+ 以支持 UUID（包含连字符）
    expr_pattern = r"^payload\.(\w+)\s*=\s*'([\w-]+)'$"
    matched = re.match(expr_pattern, filter_expr.strip())

    if not matched:
        raise ValueError(f"过滤表达式格式无效: '{filter_expr}'。期望格式: payload.field = 'value'")

    fld, val = matched.groups()

    if fld not in _FILTER_WHITELIST:
        raise ValueError(f"不允许过滤字段 '{fld}'。允许的字段: {list(_FILTER_WHITELIST.keys())}")

    allowed_values = _FILTER_WHITELIST[fld]
    # None 表示允许任意值（用于 dataset_id 等动态字段）
    if allowed_values is not None and val not in allowed_values:
        raise ValueError(f"字段 '{fld}' 的值 '{val}' 无效。允许的值: {allowed_values}")


class IndexSchema(MemoryNode):
    """索引数据点的schema定义"""

    id: str
    text: str
    # Dataset isolation: 用于 Episode Routing 的 dataset 过滤
    dataset_id: Optional[str] = None
    # Memory type: 用于 atomic/episodic 过滤
    memory_type: Optional[str] = None
    metadata: dict = {"index_fields": ["text"]}


class LanceDBAdapter(VectorProvider):
    """LanceDB向量数据库适配器实现"""

    name = "LanceDB"
    url: str
    api_key: str
    connection: lancedb.AsyncConnection = None

    def __init__(
        self,
        url: Optional[str],
        api_key: Optional[str],
        embedding_engine: EmbeddingEngine,
    ):
        self.url = url
        self.api_key = api_key
        self.embedding_engine = embedding_engine
        self._lock = asyncio.Lock()

    async def get_connection(self) -> lancedb.AsyncConnection:
        """获取或创建数据库连接"""
        if self.connection is None:
            self.connection = await lancedb.connect_async(self.url, api_key=self.api_key)
        return self.connection

    async def embed_data(self, texts: list[str]) -> list[list[float]]:
        """将文本数据转换为向量表示"""
        return await self.embedding_engine.embed_text(texts)

    async def has_collection(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        conn = await self.get_connection()
        tables = await conn.table_names()
        return collection_name in tables

    async def create_collection(self, collection_name: str, payload_schema: BaseModel) -> None:
        """创建新集合"""
        vec_dim = self.embedding_engine.get_vector_size()
        cleaned_schema = _build_stripped_schema(payload_schema, MemoryNode)
        type_hints = get_type_hints(cleaned_schema)

        class _LanceRecord(LanceModel):
            """LanceDB记录模型"""

            id: type_hints["id"]
            vector: Vector(vec_dim)
            payload: cleaned_schema

        exists = await self.has_collection(collection_name)
        if exists:
            return

        async with self._lock:
            # 双重检查锁定
            if await self.has_collection(collection_name):
                return

            conn = await self.get_connection()
            await conn.create_table(
                name=collection_name,
                schema=_LanceRecord,
                exist_ok=True,
            )

    async def get_collection(self, collection_name: str):
        """获取指定集合"""
        if not await self.has_collection(collection_name):
            raise CollectionNotFoundError(f"Collection '{collection_name}' not found!")

        conn = await self.get_connection()
        return await conn.open_table(collection_name)

    async def create_memory_nodes(self, collection_name: str, memory_nodes: list[MemoryNode]) -> None:
        """创建或更新内存节点"""
        if not memory_nodes:
            return

        schema_type = type(memory_nodes[0])

        # 确保集合存在
        if not await self.has_collection(collection_name):
            async with self._lock:
                if not await self.has_collection(collection_name):
                    await self.create_collection(collection_name, schema_type)

        coll = await self.get_collection(collection_name)

        # 提取可嵌入数据
        embeddable_items = [MemoryNode.extract_index_text(node) for node in memory_nodes]

        # 分离有效和无效索引
        valid_idxs = [i for i, item in enumerate(embeddable_items) if item is not None]
        valid_texts = [embeddable_items[i] for i in valid_idxs]

        # 生成向量
        vec_dim = self.embedding_engine.get_vector_size()
        empty_vec = [0.0] * vec_dim

        if valid_texts:
            computed_vecs = await self.embed_data(valid_texts)
        else:
            computed_vecs = []

        # 重建完整向量列表
        all_vectors: list[list[float]] = []
        valid_ptr = 0
        for item in embeddable_items:
            if item is not None:
                all_vectors.append(computed_vecs[valid_ptr])
                valid_ptr += 1
            else:
                all_vectors.append(empty_vec)

        # 构建Lance记录类型
        class _LanceNode(LanceModel, Generic[_IdT, _PayloadT]):
            """Lance内存节点"""

            id: _IdT
            vector: Vector(vec_dim)
            payload: _PayloadT

        cleaned_schema = _build_stripped_schema(schema_type, MemoryNode)

        def to_lance_record(node: MemoryNode, vec: list[float]) -> _LanceNode:
            props = get_own_properties(node)
            props["id"] = str(props["id"])
            return _LanceNode[str, cleaned_schema](
                id=str(node.id),
                vector=vec,
                payload=props,
            )

        records = [to_lance_record(node, all_vectors[idx]) for idx, node in enumerate(memory_nodes)]

        # 去重
        unique_records = list({r.id: r for r in records}.values())

        # 执行upsert
        async with self._lock:
            await (
                coll.merge_insert("id").when_matched_update_all().when_not_matched_insert_all().execute(unique_records)
            )

    async def retrieve(self, collection_name: str, memory_node_ids: list[str]) -> list[VectorSearchHit]:
        """根据ID检索节点"""
        coll = await self.get_collection(collection_name)

        # 构建查询条件
        if len(memory_node_ids) == 1:
            condition = f"id = '{memory_node_ids[0]}'"
        else:
            condition = f"id IN {tuple(memory_node_ids)}"

        query_result = await coll.query().where(condition)

        # 转换结果格式
        if hasattr(query_result, "to_list"):
            items = query_result.to_list()
        else:
            items = list(query_result)

        return [
            VectorSearchHit(
                id=parse_id(item["id"]),
                payload=item["payload"],
                score=0,
            )
            for item in items
        ]

    async def search(
        self,
        collection_name: str,
        query_text: str = None,
        query_vector: List[float] = None,
        limit: Optional[int] = 15,
        with_vector: bool = False,
        normalized: bool = True,
        where_filter: Optional[str] = None,
    ) -> list[VectorSearchHit]:
        """执行向量相似性搜索"""
        # 参数验证
        if query_text is None and query_vector is None:
            raise MissingQueryParameterError()

        # 文本转向量
        if query_text and query_vector is None:
            embeddings = await self.embedding_engine.embed_text([query_text])
            query_vector = embeddings[0]

        coll = await self.get_collection(collection_name)

        # 处理limit
        if limit is None:
            limit = await coll.count_rows()

        if limit <= 0:
            return []

        # 构建搜索查询
        search_builder = coll.vector_search(query_vector)

        if where_filter:
            _check_filter_security(where_filter)
            search_builder = search_builder.where(where_filter)

        raw_results = await search_builder.limit(limit).to_list()

        if not raw_results:
            return []

        # 提取原始距离
        distances = [r["_distance"] for r in raw_results]

        # 归一化分数
        scores = normalize_distances(raw_results)

        # 构建结果
        output: list[VectorSearchHit] = []
        for idx, r in enumerate(raw_results):
            output.append(
                VectorSearchHit(
                    id=parse_id(r["id"]),
                    payload=r["payload"],
                    score=scores[idx],
                    raw_distance=distances[idx],
                    collection_name=collection_name,
                )
            )

        return output

    async def batch_search(
        self,
        collection_name: str,
        query_texts: List[str],
        limit: Optional[int] = None,
        with_vectors: bool = False,
    ) -> list[list[VectorSearchHit]]:
        """批量向量搜索"""
        vectors = await self.embedding_engine.embed_text(query_texts)

        tasks = [
            self.search(
                collection_name=collection_name,
                query_vector=vec,
                limit=limit,
                with_vector=with_vectors,
            )
            for vec in vectors
        ]

        return await asyncio.gather(*tasks)

    async def delete_memory_nodes(self, collection_name: str, memory_node_ids: list[str]) -> None:
        """删除指定内存节点"""
        coll = await self.get_collection(collection_name)

        # 逐个删除避免冲突
        for node_id in memory_node_ids:
            await coll.delete(f"id = '{node_id}'")

    async def create_vector_index(self, index_name: str, index_property_name: str) -> None:
        """创建向量索引"""
        full_name = f"{index_name}_{index_property_name}"
        await self.create_collection(full_name, payload_schema=IndexSchema)

    async def index_memory_nodes(
        self,
        index_name: str,
        index_property_name: str,
        memory_nodes: list[MemoryNode],
    ) -> None:
        """为内存节点建立索引

        保留 dataset_id 和 memory_type 字段以支持：
        - Episode Routing 的 dataset 隔离过滤
        - Retrieval 的 memory_type 过滤
        """
        full_name = f"{index_name}_{index_property_name}"

        index_entries = [
            IndexSchema(
                id=str(node.id),
                text=getattr(node, node.metadata["index_fields"][0]),
                dataset_id=getattr(node, "dataset_id", None),
                memory_type=getattr(node, "memory_type", None),
            )
            for node in memory_nodes
        ]

        await self.create_memory_nodes(full_name, index_entries)

    async def prune(self) -> None:
        """清理所有集合和数据"""
        conn = await self.get_connection()
        table_list = await conn.table_names()

        for tbl_name in table_list:
            tbl = await self.get_collection(tbl_name)
            await tbl.delete("id IS NOT NULL")
            await conn.drop_table(tbl_name)

        # 如果是本地路径，清理文件
        if self.url.startswith("/"):
            parent_dir = path.dirname(self.url)
            db_name = path.basename(self.url)
            await get_file_storage(parent_dir).remove_all(db_name)
            # Reset connection after deleting database files
            # Next get_connection() call will create a fresh connection
            self.connection = None

    def get_memory_node_schema(self, model_type: BaseModel) -> type[BaseModel]:
        """获取内存节点的精简schema"""
        return _build_stripped_schema(model_type, MemoryNode)

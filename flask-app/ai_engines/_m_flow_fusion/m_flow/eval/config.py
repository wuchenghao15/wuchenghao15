# m_flow/eval/config.py
"""
P7-0: Evaluation Configuration and Stability Foundation

Unified management of all evaluation parameters to ensure reproducibility.
"""

from __future__ import annotations
import os
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class RetrievalConfig:
    """Retrieval parameter configuration"""

    wide_search_top_k: int = 100
    max_relevant_ids: int = 300
    edge_miss_cost: float = 0.9
    hop_cost: float = 0.05
    direct_penalty: float = 0.3
    inactive_penalty: float = 0.4


@dataclass
class InjectionConfig:
    """Injection parameter configuration"""

    max_procedural_cards: int = 3
    strong_threshold: float = 0.35
    gap_threshold: float = 0.15
    budget_chars: int = 4000
    budget_tokens: Optional[int] = None


@dataclass
class RuntimeConfig:
    """Runtime configuration"""

    trace_enabled: bool = True
    llm_concurrency: int = 1
    embedding_concurrency: int = 1
    seed: Optional[int] = 42


@dataclass
class EvalConfig:
    """
    Evaluation configuration snapshot.

    Contains all parameters affecting evaluation results, used for:
    - Ensuring evaluation reproducibility
    - Parameter consistency when comparing with baseline
    - Writing to reports for traceability
    """

    name: str = "default"
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    injection: InjectionConfig = field(default_factory=InjectionConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

    # Additional custom parameters
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for serialization)"""
        return {
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at,
            "retrieval": asdict(self.retrieval),
            "injection": asdict(self.injection),
            "runtime": asdict(self.runtime),
            "extra": self.extra,
        }

    def save(self, path: str) -> None:
        """Save configuration to file"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "EvalConfig":
        """Load configuration from file"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            name=data.get("name", "default"),
            version=data.get("version", "1.0"),
            created_at=data.get("created_at", ""),
            retrieval=RetrievalConfig(**data.get("retrieval", {})),
            injection=InjectionConfig(**data.get("injection", {})),
            runtime=RuntimeConfig(**data.get("runtime", {})),
            extra=data.get("extra", {}),
        )

    @classmethod
    def from_env(cls) -> "EvalConfig":
        """Create configuration from environment variables"""

        def _env_float(key: str, default: float) -> float:
            v = os.getenv(key)
            return float(v) if v else default

        def _env_int(key: str, default: int) -> int:
            v = os.getenv(key)
            return int(v) if v else default

        def _env_bool(key: str, default: bool) -> bool:
            v = os.getenv(key)
            if v is None:
                return default
            return v.lower() in ("1", "true", "yes")

        return cls(
            retrieval=RetrievalConfig(
                wide_search_top_k=_env_int("EVAL_WIDE_SEARCH_TOP_K", 100),
                max_relevant_ids=_env_int("EVAL_MAX_RELEVANT_IDS", 300),
                edge_miss_cost=_env_float("EVAL_EDGE_MISS_COST", 0.9),
                hop_cost=_env_float("EVAL_HOP_COST", 0.05),
            ),
            injection=InjectionConfig(
                max_procedural_cards=_env_int("EVAL_MAX_PROCEDURAL_CARDS", 3),
                strong_threshold=_env_float("EVAL_STRONG_THRESHOLD", 0.35),
            ),
            runtime=RuntimeConfig(
                trace_enabled=_env_bool("MFLOW_TRACE_ENABLED", True),
            ),
        )


class EvalSetup:
    """
    Evaluation environment setup.

    Responsibilities:
    - Prepare database (fixed corpus ingestion or load snapshot)
    - Set environment variables
    - Configure tracing
    """

    def __init__(self, config: EvalConfig):
        self.config = config

    async def prepare(self) -> None:
        """Prepare evaluation environment"""
        # Set tracing
        import os

        if self.config.runtime.trace_enabled:
            os.environ["MFLOW_TRACE_ENABLED"] = "1"
        else:
            os.environ["MFLOW_TRACE_ENABLED"] = "0"

        # Set sample rate to 100% (no sampling during evaluation)
        os.environ["MFLOW_TRACE_SAMPLE_RATE"] = "1.0"

    async def cleanup(self) -> None:
        """Clean up evaluation environment"""
        pass

    async def reset_database(self) -> None:
        """
        Reset database (optional).

        Used to ensure each evaluation starts from the same state.
        """
        # Can call m_flow's cleanup interface here
        # await m_flow.prune.prune_data()
        pass

    async def load_snapshot(self, snapshot_path: str) -> None:
        """
        Load database snapshot (optional).

        Used to quickly restore to a known state.
        """
        # Implement snapshot loading logic
        pass

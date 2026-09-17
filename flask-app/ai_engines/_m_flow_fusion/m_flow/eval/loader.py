# m_flow/eval/loader.py
"""
P7-1: Dataset Loading and Validation

Read JSONL dataset and validate schema.
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProcedureExpect:
    """Procedure expectation"""

    any_of_keys: List[str] = field(default_factory=list)
    any_of_titles_contains: List[str] = field(default_factory=list)
    at_least_one_active: bool = True


@dataclass
class EpisodicExpect:
    """Episodic expectation"""

    should_retrieve: bool = False
    any_of_episode_ids: List[str] = field(default_factory=list)


@dataclass
class AtomicExpect:
    """Atomic expectation"""

    should_retrieve: bool = False


@dataclass
class InjectionConstraints:
    """Injection constraints"""

    max_procedural_cards: Optional[int] = None
    require_context_fields: List[str] = field(default_factory=list)
    require_steps: bool = False


@dataclass
class CaseExpect:
    """Expected result"""

    should_trigger_procedural: Optional[bool] = None
    should_inject_procedural: Optional[bool] = None
    procedures: ProcedureExpect = field(default_factory=ProcedureExpect)
    episodic: EpisodicExpect = field(default_factory=EpisodicExpect)
    atomic: AtomicExpect = field(default_factory=AtomicExpect)
    injection_constraints: InjectionConstraints = field(default_factory=InjectionConstraints)


@dataclass
class ConversationContext:
    """Conversation context"""

    messages: List[Dict[str, str]] = field(default_factory=list)
    agent_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalCase:
    """Evaluation case"""

    id: str
    type: str  # explicit_procedure | implicit_task | micro_action | negative
    query: str
    conversation_ctx: ConversationContext = field(default_factory=ConversationContext)
    expect: CaseExpect = field(default_factory=CaseExpect)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "query": self.query,
            "conversation_ctx": {
                "messages": self.conversation_ctx.messages,
                "agent_state": self.conversation_ctx.agent_state,
            },
            "expect": {
                "should_trigger_procedural": self.expect.should_trigger_procedural,
                "should_inject_procedural": self.expect.should_inject_procedural,
                "procedures": {
                    "any_of_keys": self.expect.procedures.any_of_keys,
                    "any_of_titles_contains": self.expect.procedures.any_of_titles_contains,
                    "at_least_one_active": self.expect.procedures.at_least_one_active,
                },
                "episodic": {
                    "should_retrieve": self.expect.episodic.should_retrieve,
                    "any_of_episode_ids": self.expect.episodic.any_of_episode_ids,
                },
                "atomic": {
                    "should_retrieve": self.expect.atomic.should_retrieve,
                },
                "injection_constraints": {
                    "max_procedural_cards": self.expect.injection_constraints.max_procedural_cards,
                    "require_context_fields": self.expect.injection_constraints.require_context_fields,
                    "require_steps": self.expect.injection_constraints.require_steps,
                },
            },
            "notes": self.notes,
        }


class CaseLoader:
    """
    Dataset loader.

    Supports:
    - JSONL format
    - Schema validation
    - Backward compatibility with old fields
    """

    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.cases: List[EvalCase] = []
        self.errors: List[str] = []

    def load(self) -> List[EvalCase]:
        """Load dataset"""
        self.cases = []
        self.errors = []

        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    case = self._parse_case(data, line_num)
                    if case:
                        self.cases.append(case)
                except json.JSONDecodeError as e:
                    self.errors.append(f"Line {line_num}: JSON parse error: {e}")
                except Exception as e:
                    self.errors.append(f"Line {line_num}: {e}")

        return self.cases

    def _parse_case(self, data: Dict[str, Any], line_num: int) -> Optional[EvalCase]:
        """Parse a single case"""
        # Required fields
        case_id = data.get("id")
        if not case_id:
            self.errors.append(f"Line {line_num}: missing 'id'")
            return None

        query = data.get("query")
        if not query:
            self.errors.append(f"Line {line_num}: missing 'query'")
            return None

        case_type = data.get("type", "unknown")

        # Parse conversation_ctx
        ctx_data = data.get("conversation_ctx") or {}
        conversation_ctx = ConversationContext(
            messages=ctx_data.get("messages") or [],
            agent_state=ctx_data.get("agent_state") or {},
        )

        # Parse expect
        exp_data = data.get("expect") or {}

        proc_data = exp_data.get("procedures") or {}
        procedures = ProcedureExpect(
            any_of_keys=proc_data.get("any_of_keys") or [],
            any_of_titles_contains=proc_data.get("any_of_titles_contains") or [],
            at_least_one_active=proc_data.get("at_least_one_active", True),
        )

        epi_data = exp_data.get("episodic") or {}
        episodic = EpisodicExpect(
            should_retrieve=epi_data.get("should_retrieve", False),
            any_of_episode_ids=epi_data.get("any_of_episode_ids") or [],
        )

        atom_data = exp_data.get("atomic") or {}
        atomic = AtomicExpect(
            should_retrieve=atom_data.get("should_retrieve", False),
        )

        inj_data = exp_data.get("injection_constraints") or {}
        injection_constraints = InjectionConstraints(
            max_procedural_cards=inj_data.get("max_procedural_cards"),
            require_context_fields=inj_data.get("require_context_fields") or [],
            require_steps=inj_data.get("require_steps", False),
        )

        expect = CaseExpect(
            should_trigger_procedural=exp_data.get("should_trigger_procedural"),
            should_inject_procedural=exp_data.get("should_inject_procedural"),
            procedures=procedures,
            episodic=episodic,
            atomic=atomic,
            injection_constraints=injection_constraints,
        )

        return EvalCase(
            id=case_id,
            type=case_type,
            query=query,
            conversation_ctx=conversation_ctx,
            expect=expect,
            notes=data.get("notes", ""),
        )

    def get_by_type(self, case_type: str) -> List[EvalCase]:
        """Filter cases by type"""
        return [c for c in self.cases if c.type == case_type]

    def get_stats(self) -> Dict[str, int]:
        """Get dataset statistics"""
        stats = {"total": len(self.cases)}
        for c in self.cases:
            stats[c.type] = stats.get(c.type, 0) + 1
        return stats

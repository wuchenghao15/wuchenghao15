"""Semantic validator for Hyper-Extract YAML templates.

``load_template()`` only checks Pydantic shape. This module applies the checks
documented in ``hyperextract-skills/yaml-validator/`` so authors can catch
identifier, display, and spatiotemporal mistakes before extraction.

Each ``HE-T*`` rule points at the matching skill file and
``hyperextract/templates/DESIGN_GUIDE.md`` section. Lookup of fixes:
``hyperextract-skills/yaml-validator/references/rules-errors.md`` and
DESIGN_GUIDE Part 5 Common Errors.

The runtime loader is intentionally left unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import ValidationError

from .gallery import Gallery
from .parsers.loader import TemplateCfg, localize_template
from .parsers.schemas.base import FieldSchema
from .parsers.schemas.graph import (
    GraphDisplaySchema,
    GraphIdentifiersSchema,
    GraphOutputSchema,
)
from .parsers.schemas.naive import (
    NaiveDisplaySchema,
    NaiveIdentifierSchema,
    NaiveOutputSchema,
)

Severity = Literal["error", "warning"]

HE_T001 = "HE-T001"  # YAML syntax
HE_T002 = "HE-T002"  # TemplateCfg / schema
HE_T003 = "HE-T003"  # identifier field reference
HE_T004 = "HE-T004"  # relation_members type mismatch
HE_T005 = "HE-T005"  # display placeholder
HE_T006 = "HE-T006"  # missing time_field / location_field
HE_T007 = "HE-T007"  # bilingual completeness
HE_T008 = "HE-T008"  # field count > DESIGN_GUIDE limit
HE_T009 = "HE-T009"  # Gallery domain/name collision

GRAPH_TYPES = frozenset(
    {
        "graph",
        "hypergraph",
        "temporal_graph",
        "spatial_graph",
        "spatio_temporal_graph",
    }
)
BINARY_GRAPH_TYPES = frozenset(
    {"graph", "temporal_graph", "spatial_graph", "spatio_temporal_graph"}
)
TEMPORAL_TYPES = frozenset({"temporal_graph", "spatio_temporal_graph"})
SPATIAL_TYPES = frozenset({"spatial_graph", "spatio_temporal_graph"})
RECORD_TYPES = frozenset({"model", "list", "set", "document"})

FIELD_COUNT_LIMIT = 5
_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
_LANG_KEY_RE = re.compile(r"^[a-z]{2}(?:-[A-Za-z]+)?$")


@dataclass(frozen=True)
class Diagnostic:
    """A single validator finding."""

    code: str
    severity: Severity
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }


@dataclass
class ValidationResult:
    """Outcome of validating one template file."""

    file: str
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(d.severity == "error" for d in self.diagnostics)

    @property
    def error_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == "warning")

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "ok": self.ok,
        }


def _presets_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "templates" / "presets"


def iter_template_files(path: str | Path) -> list[Path]:
    """Return YAML template files under ``path`` (file or directory), sorted."""
    root = Path(path)
    if root.is_file():
        return [root]
    files = [
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in {".yaml", ".yml"}
    ]
    return sorted(files)


def validate_template_dir(directory: str | Path) -> list[ValidationResult]:
    """Validate every YAML file under ``directory``."""
    return [validate_template(p) for p in iter_template_files(directory)]


def validate_template(path: str | Path) -> ValidationResult:
    """Validate one template YAML file (HE-T001 through HE-T009).

    Returns a :class:`ValidationResult`. ``ok`` is True when there are no
    error-severity diagnostics (warnings do not fail the result).

    See also:
        hyperextract-skills/yaml-validator/SKILL.md
        hyperextract-skills/yaml-validator/references/rules-errors.md
        hyperextract/templates/DESIGN_GUIDE.md (Part 5 Validation, Common Errors)
    """
    file_path = Path(path)
    result = ValidationResult(file=str(file_path))

    if not file_path.exists():
        result.diagnostics.append(
            Diagnostic(
                HE_T001,
                "error",
                "",
                f"File not found: {file_path}",
            )
        )
        return result

    raw, load_diags = _load_yaml(file_path)
    result.diagnostics.extend(load_diags)
    if raw is None:
        return result

    config, schema_diags = _parse_config(raw)
    result.diagnostics.extend(schema_diags)
    if config is None:
        return result

    result.diagnostics.extend(_check_localize(config))
    result.diagnostics.extend(_check_output_shape(config))
    result.diagnostics.extend(_check_identifiers(config))
    result.diagnostics.extend(_check_spatiotemporal(config))
    result.diagnostics.extend(_check_display(config))
    result.diagnostics.extend(_check_bilingual(config))
    result.diagnostics.extend(_check_field_count(config))
    result.diagnostics.extend(_check_gallery_collision(file_path, config))
    return result


def _load_yaml(path: Path) -> tuple[dict[str, Any] | None, list[Diagnostic]]:
    """Parse YAML text (HE-T001).

    See also:
        hyperextract-skills/yaml-validator/references/rules-syntax.md
        hyperextract/templates/DESIGN_GUIDE.md (Part 5 Validation)
    """
    try:
        with open(path, encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        loc = ""
        mark = getattr(exc, "problem_mark", None)
        if mark is not None:
            loc = f"line {mark.line + 1}"
        return None, [
            Diagnostic(HE_T001, "error", loc, f"YAML is not parseable: {exc}")
        ]
    except OSError as exc:
        return None, [Diagnostic(HE_T001, "error", "", f"Cannot read file: {exc}")]

    if raw is None:
        return None, [Diagnostic(HE_T002, "error", "", "Template YAML is empty")]
    if not isinstance(raw, dict):
        return None, [
            Diagnostic(
                HE_T002,
                "error",
                "",
                "Template YAML must be a mapping of keys to values",
            )
        ]
    return raw, []


def _parse_config(
    raw: dict[str, Any],
) -> tuple[TemplateCfg | None, list[Diagnostic]]:
    """Match the document to ``TemplateCfg`` (HE-T002).

    See also:
        hyperextract-skills/yaml-validator/references/rules-types.md
        hyperextract/templates/DESIGN_GUIDE.md (Part 2 Type-Specific Design)
    """
    try:
        return TemplateCfg(**raw), []
    except ValidationError as exc:
        diags = []
        for err in exc.errors():
            loc = ".".join(str(part) for part in err.get("loc", ()))
            diags.append(
                Diagnostic(HE_T002, "error", loc, err.get("msg", "Invalid template"))
            )
        if not diags:
            diags.append(Diagnostic(HE_T002, "error", "", "Invalid template schema"))
        return None, diags
    except (TypeError, ValueError) as exc:
        return None, [Diagnostic(HE_T002, "error", "", str(exc))]


def _check_localize(config: TemplateCfg) -> list[Diagnostic]:
    languages = (
        config.language if isinstance(config.language, list) else [config.language]
    )
    diags: list[Diagnostic] = []
    for lang in languages:
        try:
            localize_template(config, lang)
        except Exception as exc:
            diags.append(
                Diagnostic(
                    HE_T002,
                    "error",
                    "language",
                    f"Template is not valid for language {lang!r}: {exc}",
                )
            )
    return diags


def _check_output_shape(config: TemplateCfg) -> list[Diagnostic]:
    """Require type-specific output keys (HE-T002).

    See also:
        hyperextract-skills/yaml-validator/references/rules-types.md
        hyperextract/templates/DESIGN_GUIDE.md (Part 2 Type-Specific Design)
    """
    if config.type in GRAPH_TYPES and not isinstance(config.output, GraphOutputSchema):
        return [
            Diagnostic(
                HE_T002,
                "error",
                "output",
                f"{config.type} templates require output.entities and output.relations",
            )
        ]
    if config.type in RECORD_TYPES and not isinstance(config.output, NaiveOutputSchema):
        return [
            Diagnostic(
                HE_T002,
                "error",
                "output",
                f"{config.type} templates require output.fields",
            )
        ]
    return []


def _field_map(schema: NaiveOutputSchema) -> dict[str, FieldSchema]:
    return {item.name: item for item in schema.fields}


def _field_refs(spec: str | None, *, placeholders_only: bool = False) -> list[str]:
    """Return field names referenced by an identifier or display string.

    Identifiers treat a bare name (``name``) as a field. Display strings only
    contribute ``{placeholder}`` matches; a constant label with no braces is
    allowed.
    """
    if not spec:
        return []
    if "{" in spec:
        return _PLACEHOLDER_RE.findall(spec)
    if placeholders_only:
        return []
    return [spec]


def _missing_fields(
    spec: str,
    available: set[str],
    *,
    placeholders_only: bool = False,
) -> list[str]:
    return [
        name
        for name in _field_refs(spec, placeholders_only=placeholders_only)
        if name not in available
    ]


def _entity_relation_fields(
    config: TemplateCfg,
) -> tuple[set[str], set[str]] | None:
    if not isinstance(config.output, GraphOutputSchema):
        return None
    return (
        set(_field_map(config.output.entities)),
        set(_field_map(config.output.relations)),
    )


def _record_fields(config: TemplateCfg) -> set[str]:
    if not isinstance(config.output, NaiveOutputSchema):
        return set()
    return set(_field_map(config.output))


def _check_identifiers(config: TemplateCfg) -> list[Diagnostic]:
    """Check identifier field references (HE-T003).

    See also:
        hyperextract-skills/yaml-validator/references/rules-identifiers.md
        hyperextract/templates/DESIGN_GUIDE.md (Part 3 Identifiers Configuration)
    """
    if config.type in RECORD_TYPES:
        return _check_record_identifiers(config)
    if config.type in GRAPH_TYPES:
        return _check_graph_identifiers(config)
    return []


def _check_record_identifiers(config: TemplateCfg) -> list[Diagnostic]:
    if config.type != "set":
        return []

    diags: list[Diagnostic] = []
    identifiers = config.identifiers
    item_id = getattr(identifiers, "item_id", None) if identifiers else None
    if not item_id:
        diags.append(
            Diagnostic(
                HE_T003,
                "error",
                "identifiers.item_id",
                "set templates require identifiers.item_id",
            )
        )
        return diags

    available = _record_fields(config)
    missing = _missing_fields(item_id, available)
    for name in missing:
        diags.append(
            Diagnostic(
                HE_T003,
                "error",
                "identifiers.item_id",
                f"Field {name!r} is not defined in output.fields",
            )
        )
    return diags


def _check_graph_identifiers(config: TemplateCfg) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    identifiers = config.identifiers
    if identifiers is None:
        diags.append(
            Diagnostic(
                HE_T003,
                "error",
                "identifiers",
                f"{config.type} templates require an identifiers section",
            )
        )
        return diags

    if isinstance(identifiers, NaiveIdentifierSchema):
        diags.append(
            Diagnostic(
                HE_T003,
                "error",
                "identifiers",
                f"{config.type} templates require entity_id, relation_id, "
                "and relation_members (not item_id)",
            )
        )
        return diags

    fields = _entity_relation_fields(config)
    if fields is None:
        return diags
    entity_fields, relation_fields = fields

    entity_id = getattr(identifiers, "entity_id", None)
    relation_id = getattr(identifiers, "relation_id", None)
    relation_members = getattr(identifiers, "relation_members", None)

    if not entity_id:
        diags.append(
            Diagnostic(
                HE_T003,
                "error",
                "identifiers.entity_id",
                "entity_id is required for graph templates",
            )
        )
    else:
        for name in _missing_fields(entity_id, entity_fields):
            diags.append(
                Diagnostic(
                    HE_T003,
                    "error",
                    "identifiers.entity_id",
                    f"Field {name!r} is not defined in output.entities",
                )
            )

    if not relation_id:
        diags.append(
            Diagnostic(
                HE_T003,
                "error",
                "identifiers.relation_id",
                "relation_id is required for graph templates",
            )
        )
    else:
        for name in _missing_fields(relation_id, relation_fields):
            diags.append(
                Diagnostic(
                    HE_T003,
                    "error",
                    "identifiers.relation_id",
                    f"Field {name!r} is not defined in output.relations",
                )
            )

    diags.extend(
        _check_relation_members(config.type, relation_members, relation_fields, config)
    )
    return diags


def _check_relation_members(
    autotype: str,
    members: Any,
    relation_fields: set[str],
    config: TemplateCfg,
) -> list[Diagnostic]:
    """Check ``relation_members`` shape vs AutoType (HE-T004).

    Binary graph types require a dict whose values name edge-schema fields
    (direction preserved). Hypergraph requires a string or list of list-typed
    relation fields, not a dict.

    See also:
        hyperextract-skills/yaml-validator/references/rules-identifiers.md
            (Binary Relations, Hypergraph)
        hyperextract/templates/DESIGN_GUIDE.md
            (Part 2 graph vs hypergraph)
    """
    diags: list[Diagnostic] = []
    if members is None:
        diags.append(
            Diagnostic(
                HE_T003,
                "error",
                "identifiers.relation_members",
                "relation_members is required for graph templates",
            )
        )
        return diags

    if autotype in BINARY_GRAPH_TYPES:
        if not isinstance(members, dict):
            diags.append(
                Diagnostic(
                    HE_T004,
                    "error",
                    "identifiers.relation_members",
                    f"{autotype} requires relation_members to be a dict "
                    "mapping roles to edge field names",
                )
            )
            return diags
        if not members:
            diags.append(
                Diagnostic(
                    HE_T003,
                    "error",
                    "identifiers.relation_members",
                    "relation_members dict must map at least one edge field",
                )
            )
            return diags
        # The extractor (parsers/identifiers.py) reads members["source"] and
        # members["target"] directly, so both roles are required — otherwise the
        # template validates but raises KeyError at extraction time.
        for required_role in ("source", "target"):
            if required_role not in members:
                diags.append(
                    Diagnostic(
                        HE_T003,
                        "error",
                        "identifiers.relation_members",
                        f"Binary graph relation_members must define a "
                        f"{required_role!r} role",
                    )
                )
        for role, field_name in members.items():
            if field_name not in relation_fields:
                diags.append(
                    Diagnostic(
                        HE_T003,
                        "error",
                        f"identifiers.relation_members.{role}",
                        f"Field {field_name!r} is not defined in output.relations",
                    )
                )
        return diags

    if autotype == "hypergraph":
        if isinstance(members, dict):
            diags.append(
                Diagnostic(
                    HE_T004,
                    "error",
                    "identifiers.relation_members",
                    "hypergraph requires relation_members to be a string "
                    "or a list of field names, not a dict",
                )
            )
            return diags
        if isinstance(members, str):
            names = [members] if members else []
        elif isinstance(members, list):
            names = list(members)
        else:
            diags.append(
                Diagnostic(
                    HE_T004,
                    "error",
                    "identifiers.relation_members",
                    "hypergraph requires relation_members to be a string or list",
                )
            )
            return diags
        if not names:
            diags.append(
                Diagnostic(
                    HE_T003,
                    "error",
                    "identifiers.relation_members",
                    "relation_members must name at least one relation field",
                )
            )
            return diags

        relation_schema = (
            _field_map(config.output.relations)
            if isinstance(config.output, GraphOutputSchema)
            else {}
        )
        for name in names:
            if name not in relation_fields:
                diags.append(
                    Diagnostic(
                        HE_T003,
                        "error",
                        "identifiers.relation_members",
                        f"Field {name!r} is not defined in output.relations",
                    )
                )
                continue
            field_schema = relation_schema.get(name)
            if field_schema is not None and field_schema.type != "list":
                diags.append(
                    Diagnostic(
                        HE_T004,
                        "error",
                        "identifiers.relation_members",
                        f"Hypergraph member field {name!r} must have type: list",
                    )
                )
        return diags

    return diags


def _check_spatiotemporal(config: TemplateCfg) -> list[Diagnostic]:
    """Require ``time_field`` / ``location_field`` (HE-T006).

    See also:
        hyperextract-skills/yaml-validator/references/rules-identifiers.md
            (Temporal Graph, Spatial Graph)
        hyperextract/templates/DESIGN_GUIDE.md
            (Part 2 temporal_graph / spatial_graph)
    """
    if config.type not in TEMPORAL_TYPES | SPATIAL_TYPES:
        return []
    if not isinstance(config.identifiers, GraphIdentifiersSchema):
        # Missing/wrong identifiers already reported as HE-T003.
        return []

    diags: list[Diagnostic] = []
    fields = _entity_relation_fields(config)
    relation_fields = fields[1] if fields else set()

    if config.type in TEMPORAL_TYPES:
        time_field = config.identifiers.time_field
        if not time_field:
            diags.append(
                Diagnostic(
                    HE_T006,
                    "error",
                    "identifiers.time_field",
                    f"{config.type} requires identifiers.time_field",
                )
            )
        else:
            for name in _missing_fields(time_field, relation_fields):
                diags.append(
                    Diagnostic(
                        HE_T003,
                        "error",
                        "identifiers.time_field",
                        f"Field {name!r} is not defined in output.relations",
                    )
                )

    if config.type in SPATIAL_TYPES:
        location_field = config.identifiers.location_field
        if not location_field:
            diags.append(
                Diagnostic(
                    HE_T006,
                    "error",
                    "identifiers.location_field",
                    f"{config.type} requires identifiers.location_field",
                )
            )
        else:
            for name in _missing_fields(location_field, relation_fields):
                diags.append(
                    Diagnostic(
                        HE_T003,
                        "error",
                        "identifiers.location_field",
                        f"Field {name!r} is not defined in output.relations",
                    )
                )
    return diags


def _check_display(config: TemplateCfg) -> list[Diagnostic]:
    """Check display ``{placeholder}`` names (HE-T005).

    See also:
        hyperextract-skills/yaml-validator/SKILL.md (Field validation)
        hyperextract/templates/DESIGN_GUIDE.md (Part 3 Display Configuration)
    """
    display = config.display
    diags: list[Diagnostic] = []

    if isinstance(display, NaiveDisplaySchema):
        available = _record_fields(config)
        for name in _missing_fields(display.label, available, placeholders_only=True):
            diags.append(
                Diagnostic(
                    HE_T005,
                    "error",
                    "display.label",
                    f"Placeholder {{{name}}} is not defined in output.fields",
                )
            )
        return diags

    if not isinstance(display, GraphDisplaySchema):
        return diags

    fields = _entity_relation_fields(config)
    if fields is None:
        return diags
    entity_fields, relation_fields = fields

    for name in _missing_fields(
        display.entity_label, entity_fields, placeholders_only=True
    ):
        diags.append(
            Diagnostic(
                HE_T005,
                "error",
                "display.entity_label",
                f"Placeholder {{{name}}} is not defined in output.entities",
            )
        )
    for name in _missing_fields(
        display.relation_label, relation_fields, placeholders_only=True
    ):
        diags.append(
            Diagnostic(
                HE_T005,
                "error",
                "display.relation_label",
                f"Placeholder {{{name}}} is not defined in output.relations",
            )
        )
    return diags


def _declared_languages(config: TemplateCfg) -> list[str]:
    if isinstance(config.language, list):
        return [str(lang) for lang in config.language]
    return [str(config.language)]


def _is_lang_dict(value: object) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    return all(isinstance(key, str) and _LANG_KEY_RE.match(key) for key in value)


def _walk_bilingual(value: Any, path: str, langs: list[str]) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    if _is_lang_dict(value):
        for lang in langs:
            entry = value.get(lang)
            missing = lang not in value or entry is None or entry == "" or entry == []
            if missing:
                diags.append(
                    Diagnostic(
                        HE_T007,
                        "warning",
                        f"{path}.{lang}" if path else lang,
                        f"Missing {lang!r} text on a bilingual field",
                    )
                )
        return diags
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            diags.extend(_walk_bilingual(child, child_path, langs))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            diags.extend(_walk_bilingual(child, f"{path}[{index}]", langs))
    return diags


def _check_bilingual(config: TemplateCfg) -> list[Diagnostic]:
    """Warn when declared languages are missing on bilingual fields (HE-T007).

    See also:
        hyperextract/templates/DESIGN_GUIDE.md (Part 4 Multi-language Rules)
    """
    langs = _declared_languages(config)
    payload = {
        "description": config.description,
        "output": config.output.model_dump(),
        "guideline": config.guideline.model_dump(),
    }
    return _walk_bilingual(payload, "", langs)


def _check_field_count(config: TemplateCfg) -> list[Diagnostic]:
    """Warn when field count exceeds the DESIGN_GUIDE Part 4 limit (HE-T008).

    Graph types check entity and relation schemas. Naive types
    (``model`` / ``list`` / ``set``) check ``output.fields``. The cap is
    ``FIELD_COUNT_LIMIT`` (Part 4: max 5 fields per component).

    See also:
        hyperextract-skills/yaml-validator/SKILL.md (Validation Levels)
        hyperextract/templates/DESIGN_GUIDE.md
            (Quick Reference Field Count Guidelines, Part 4 Field Count Optimization)
    """
    diags: list[Diagnostic] = []
    if isinstance(config.output, GraphOutputSchema):
        entity_count = len(config.output.entities.fields)
        relation_count = len(config.output.relations.fields)
        if entity_count > FIELD_COUNT_LIMIT:
            diags.append(
                Diagnostic(
                    HE_T008,
                    "warning",
                    "output.entities.fields",
                    f"Entity schema has {entity_count} fields "
                    f"(DESIGN_GUIDE limit is {FIELD_COUNT_LIMIT})",
                )
            )
        if relation_count > FIELD_COUNT_LIMIT:
            diags.append(
                Diagnostic(
                    HE_T008,
                    "warning",
                    "output.relations.fields",
                    f"Relation schema has {relation_count} fields "
                    f"(DESIGN_GUIDE limit is {FIELD_COUNT_LIMIT})",
                )
            )
        return diags
    if config.type in RECORD_TYPES and isinstance(config.output, NaiveOutputSchema):
        count = len(config.output.fields)
        if count > FIELD_COUNT_LIMIT:
            diags.append(
                Diagnostic(
                    HE_T008,
                    "warning",
                    "output.fields",
                    f"{config.type} schema has {count} fields "
                    f"(DESIGN_GUIDE limit is {FIELD_COUNT_LIMIT})",
                )
            )
    return diags


def _is_under_presets(path: Path) -> bool:
    try:
        path.resolve().relative_to(_presets_dir().resolve())
        return True
    except ValueError:
        return False


def _domain_for(path: Path) -> str:
    presets = _presets_dir()
    try:
        relative = path.resolve().relative_to(presets.resolve())
        if relative.parts:
            return relative.parts[0]
    except ValueError:
        pass
    return path.parent.name


@lru_cache(maxsize=1)
def _preset_key_index() -> dict[str, tuple[Path, ...]]:
    presets = _presets_dir()
    index: dict[str, list[Path]] = {}
    if not presets.is_dir():
        return {}
    for file_path in presets.rglob("*.yaml"):
        try:
            with open(file_path, encoding="utf-8") as handle:
                raw = yaml.safe_load(handle)
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(raw, dict) or "name" not in raw:
            continue
        domain = file_path.parent.relative_to(presets).parts[0]
        index.setdefault(f"{domain}/{raw['name']}", []).append(file_path)
    return {key: tuple(paths) for key, paths in index.items()}


def _preset_files_for_key(key: str) -> list[Path]:
    return list(_preset_key_index().get(key, ()))


def _check_gallery_collision(path: Path, config: TemplateCfg) -> list[Diagnostic]:
    """Warn when ``domain/name`` collides with a Gallery preset (HE-T009).

    See also:
        hyperextract/templates/DESIGN_GUIDE.md (Appendix Template Directory Structure)
    """
    domain = _domain_for(path)
    if not domain:
        return []
    key = f"{domain}/{config.name}"
    if _is_under_presets(path):
        others = [
            other
            for other in _preset_files_for_key(key)
            if other.resolve() != path.resolve()
        ]
        if not others:
            return []
        return [
            Diagnostic(
                HE_T009,
                "warning",
                "name",
                f"Gallery key {key!r} is used by another preset: {others[0]}",
            )
        ]

    if key in Gallery.list():
        return [
            Diagnostic(
                HE_T009,
                "warning",
                "name",
                f"Gallery already has a template named {key!r}",
            )
        ]
    return []


__all__ = [
    "BINARY_GRAPH_TYPES",
    "FIELD_COUNT_LIMIT",
    "GRAPH_TYPES",
    "HE_T001",
    "HE_T002",
    "HE_T003",
    "HE_T004",
    "HE_T005",
    "HE_T006",
    "HE_T007",
    "HE_T008",
    "HE_T009",
    "Diagnostic",
    "ValidationResult",
    "iter_template_files",
    "validate_template",
    "validate_template_dir",
]

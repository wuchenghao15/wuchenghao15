"""
Dynamic BAML type generation from Pydantic models.

This module provides utilities to convert Pydantic model definitions into
BAML TypeBuilder representations for structured LLM output generation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Type, get_args, get_origin

from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from pydantic import BaseModel

_log = get_logger()

# Mapping from Python primitive types to BAML builder methods
_PRIMITIVE_TYPE_HANDLERS = {
    str: "string",
    int: "int",
    float: "float",
    bool: "bool",
    datetime: "string",  # BAML lacks native datetime support
}


def _check_enum_class(candidate: Any) -> bool:
    """Determine if candidate is an Enum subclass (not instance)."""
    if not isinstance(candidate, type):
        return False
    return issubclass(candidate, Enum)


def _resolve_primitive(type_builder, python_type: Type) -> Any:
    """Convert a Python primitive type to its BAML equivalent."""
    handler_name = _PRIMITIVE_TYPE_HANDLERS.get(python_type)
    if handler_name is None:
        return None
    builder_method = getattr(type_builder, handler_name)
    return builder_method()


def _build_enum_type(type_builder, enum_cls: Type[Enum]) -> Any:
    """Register an Enum and return its BAML type representation."""
    enum_type_name = enum_cls.__name__
    enum_def = type_builder.add_enum(enum_type_name)
    for item in enum_cls:
        enum_def.add_value(item.name)
    return enum_def.type()


def _handle_pydantic_nested(type_builder, model_cls: Type["BaseModel"]) -> Any:
    """Process a nested Pydantic model, creating or retrieving its BAML class."""
    from baml_py.baml_py import ClassBuilder as _ClassBuilder

    class_name = model_cls.__name__

    try:
        nested_def = type_builder.add_class(class_name)
        create_dynamic_baml_type(type_builder, nested_def, model_cls)
    except ValueError:
        nested_def = type_builder._tb.class_(class_name)

    # Handle different return mechanisms based on object type
    if isinstance(nested_def, _ClassBuilder):
        return nested_def.field()
    return nested_def.type()


class _TypeMapper:
    """
    Converts Python/Pydantic types into BAML TypeBuilder representations.

    This class handles the recursive type conversion needed for complex
    type annotations including generics, unions, and nested models.
    """

    def __init__(self, type_builder):
        self._tb = type_builder

    def convert(self, annotation: Any, field_meta: Any) -> Any:
        """
        Main entry point for type conversion.

        Args:
            annotation: The Python type annotation to convert
            field_meta: Pydantic field metadata (for additional context)

        Returns:
            BAML type representation
        """
        type_origin = get_origin(annotation)
        type_params = get_args(annotation)

        # Process Union/Optional types
        if self._is_union_origin(type_origin):
            return self._process_union(type_params, field_meta)

        # Process container types
        if type_origin is list:
            return self._process_list(type_params, field_meta)

        if type_origin is dict:
            return self._process_dict(type_params, field_meta)

        # Process Enum types
        if _check_enum_class(annotation):
            return _build_enum_type(self._tb, annotation)

        # Process nested Pydantic models
        if self._is_pydantic_model(annotation):
            return _handle_pydantic_nested(self._tb, annotation)

        # Process primitives
        primitive_result = _resolve_primitive(self._tb, annotation)
        if primitive_result is not None:
            return primitive_result

        raise ValueError(f"Cannot convert type to BAML representation: {annotation}")

    def _is_union_origin(self, origin: Any) -> bool:
        """Check if origin represents a Union type."""
        try:
            from typing import Union

            return origin is Union
        except ImportError:
            return False

    def _is_pydantic_model(self, cls: Any) -> bool:
        """Check if cls is a Pydantic BaseModel subclass."""
        from pydantic import BaseModel

        return isinstance(cls, type) and issubclass(cls, BaseModel)

    def _process_union(self, params: tuple, field_meta: Any) -> Any:
        """Handle Union[A, B, ...] and Optional[T] types."""
        real_types = [t for t in params if t is not type(None)]

        # Optional[T] is Union[T, None] with exactly 2 args
        if len(params) == 2 and len(real_types) == 1:
            inner_type = self.convert(real_types[0], field_meta)
            return inner_type.optional()

        # General union with multiple types
        converted = [self.convert(t, field_meta) for t in params]
        return self._tb.union(*converted)

    def _process_list(self, params: tuple, field_meta: Any) -> Any:
        """Handle list[T] type annotations."""
        if not params:
            raise ValueError("List type requires a type parameter")
        element_type = params[0]
        inner = self.convert(element_type, field_meta)
        return inner.list()

    def _process_dict(self, params: tuple, field_meta: Any) -> Any:
        """Handle dict[K, V] type annotations."""
        if len(params) < 2:
            key_type, val_type = str, object
        else:
            key_type, val_type = params[0], params[1]

        # Validate key type
        if key_type is not str and not _check_enum_class(key_type):
            raise ValueError(f"BAML map keys must be str or Enum subclass, got: {key_type}")

        key_baml = self.convert(key_type, field_meta)
        val_baml = self.convert(val_type, field_meta)
        return self._tb.map(key_baml, val_baml)


def create_dynamic_baml_type(tb, baml_model, pydantic_model) -> Any:
    """
    Populate a BAML model definition from a Pydantic model's fields.

    For simple string types, adds a single 'text' property. For complex
    Pydantic models, recursively converts all field annotations to their
    BAML equivalents.

    Args:
        tb: BAML TypeBuilder instance
        baml_model: Target BAML model to populate
        pydantic_model: Source Pydantic model class or str type

    Returns:
        The TypeBuilder instance (for chaining)
    """
    # Handle simple string passthrough
    if pydantic_model is str:
        baml_model.add_property("text", tb.string())
        return tb

    mapper = _TypeMapper(tb)
    model_fields = pydantic_model.model_fields

    for name, info in model_fields.items():
        field_annotation = info.annotation
        baml_type_repr = mapper.convert(field_annotation, info)

        prop_def = baml_model.add_property(name, baml_type_repr)

        # Attach description metadata if present
        if info.description:
            prop_def.description(info.description)

    return tb

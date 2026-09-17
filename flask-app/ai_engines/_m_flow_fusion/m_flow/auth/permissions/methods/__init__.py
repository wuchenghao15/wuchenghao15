"""
Access control helpers.

Functions for permission checks, grants, and dataset authorization.
"""

from __future__ import annotations

# Permission verification
from .check_permission_on_dataset import check_permission_on_dataset as check_permission_on_dataset

# Concurrency-safe permission helpers
from ._get_or_create_permission import get_or_create_permission as get_or_create_permission

# Permission granting
from .authorized_give_permission_on_datasets import (
    authorized_give_permission_on_datasets as authorized_give_permission_on_datasets,
)
from .give_permission_on_dataset import give_permission_on_dataset as give_permission_on_dataset

# Default permission setup
from .give_default_permission_to_role import give_default_permission_to_role as give_default_permission_to_role
from .give_default_permission_to_tenant import give_default_permission_to_tenant as give_default_permission_to_tenant
from .give_default_permission_to_user import give_default_permission_to_user as give_default_permission_to_user

# Principal and dataset lookups
from .get_all_user_permission_datasets import get_all_user_permission_datasets as get_all_user_permission_datasets
from .get_document_ids_for_user import get_document_ids_for_user as get_document_ids_for_user
from .get_principal import get_principal as get_principal
from .get_principal_datasets import get_principal_datasets as get_principal_datasets
from .get_role import get_role as get_role
from .get_specific_user_permission_datasets import (
    get_specific_user_permission_datasets as get_specific_user_permission_datasets,
)
from .get_tenant import get_tenant as get_tenant

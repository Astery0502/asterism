"""Compatibility exports for the split runtime registries."""

from .case_registry import CaseSpec
from .framework_registry import FrameworkCatalog, resolve_relative

__all__ = ["CaseSpec", "FrameworkCatalog", "resolve_relative"]

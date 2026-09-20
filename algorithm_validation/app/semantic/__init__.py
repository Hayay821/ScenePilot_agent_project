"""
语义理解模块
"""

from .base import SemanticProvider
from .mock import MockSemanticProvider
from .dashscope_vl import DashScopeVLSemanticProvider

__all__ = [
    "SemanticProvider",
    "MockSemanticProvider",
    "DashScopeVLSemanticProvider",
]

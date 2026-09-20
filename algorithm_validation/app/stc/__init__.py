"""
STC 模块
"""

from .base import STCAdapter
from .heuristic import HeuristicSTC

__all__ = [
    "STCAdapter",
    "HeuristicSTC",
]

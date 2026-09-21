"""
Provider module initialization
"""

from .mock import MockProvider
from .bailian import BailianProvider, create_from_config

try:
    from .dashscope_provider import DashScopeProvider
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    DashScopeProvider = None

__all__ = [
    "MockProvider",
    "BailianProvider",
    "create_from_config",
]

if DASHSCOPE_AVAILABLE:
    __all__.append("DashScopeProvider")

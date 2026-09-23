"""
ScenePilot Fast - Multi-Agent System

This package contains all agent modules for the ScenePilot Fast system.
Each agent is organized in its own subdirectory for better modularity.
"""

from .skills_manager_agent.skills_manager import SkillsManagerAgent
from .director_agent.director import DirectorAgent
from .cinematographer_agent.cinematographer import CinematographerAgent
from .editor_agent.editor import EditorAgent

__all__ = [
    'SkillsManagerAgent',
    'DirectorAgent',
    'CinematographerAgent',
    'EditorAgent',
]

__version__ = '1.1.0'

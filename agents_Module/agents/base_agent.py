"""
Base Agent

Abstract base class for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from ..schemas import AgentResult, AgentType


class BaseAgent(ABC):
    """
    Abstract base agent

    All four agents inherit from this base class.
    """

    def __init__(
        self,
        agent_type: AgentType,
        model_provider: Optional[Any] = None,
    ):
        """
        Initialize base agent

        Args:
            agent_type: Type of agent
            model_provider: Model provider for LLM calls
        """
        self.agent_type = agent_type
        self.model_provider = model_provider

    @abstractmethod
    def process(self, context: Dict[str, Any]) -> AgentResult:
        """
        Process input and generate result

        Args:
            context: Input context dictionary

        Returns:
            AgentResult with output
        """
        pass

    def _create_result(
        self,
        session_id: str,
        intent_id: Optional[str],
        output: Any,
        confidence: float = 0.0,
        **kwargs
    ) -> AgentResult:
        """
        Create standardized agent result

        Args:
            session_id: Session identifier
            intent_id: Intent identifier
            output: Agent output (dict or Pydantic model)
            confidence: Confidence score
            **kwargs: Additional AgentResult fields

        Returns:
            AgentResult
        """
        result_id = f"{self.agent_type.value}_{uuid.uuid4().hex[:8]}"

        # Convert Pydantic models to dict
        if hasattr(output, "model_dump"):
            output_dict = output.model_dump()
        else:
            output_dict = output

        return AgentResult(
            agent_name=self.agent_type,
            result_id=result_id,
            session_id=session_id,
            intent_id=intent_id,
            output=output_dict,
            confidence=confidence,
            model_provider=self.model_provider.__class__.__name__ if self.model_provider else None,
            **kwargs
        )

    def _add_teaching_notes(
        self,
        result: AgentResult,
        notes: list[str],
        user_level: str = "beginner"
    ):
        """Add teaching notes to result"""
        result.teaching_notes = notes
        result.user_level = user_level

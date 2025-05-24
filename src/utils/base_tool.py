"""
Base Tool class for the Podcast Digest project.
"""

from typing import Any

from pydantic import BaseModel


class Tool(BaseModel):
    """Base class for tools that agents can use."""

    name: str
    description: str

    def run(self, **kwargs: Any) -> Any:
        """Execute the tool's functionality."""
        raise NotImplementedError("Tool must implement run method")

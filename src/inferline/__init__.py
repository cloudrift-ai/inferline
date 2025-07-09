"""
InferLine: A pull-based LLM router with long polling capabilities.

This package provides a comprehensive solution for routing LLM requests
using a pull-based architecture where LLM providers actively poll for
tasks from a central queue.
"""

from .version import __version__

__all__ = ["__version__"]
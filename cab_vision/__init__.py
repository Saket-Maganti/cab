"""CAB-Vision: a computer-vision-native causal decision benchmark for multimodal agents.

This is the new CVPR-direction package. It is intentionally isolated from the
existing ``causal_agent_bench`` (text/tool) package so the text benchmark keeps
working while the vision benchmark is built up. See ``docs/CVPR_*`` for the full
conversion plan.

Status: prototype. No paid APIs, no large datasets, no heavy vision deps.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.0.1.dev0"

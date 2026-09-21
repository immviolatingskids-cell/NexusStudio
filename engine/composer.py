"""Prompt-preview composition from canonical identity plus a resolved take."""

from __future__ import annotations

from engine.prompts import compose_prompt_document
from engine.scene_models import ResolvedScene


def compose_prompt(scene: ResolvedScene) -> str:
    return compose_prompt_document(scene).render()


def compose_negative_prompt(scene: ResolvedScene) -> str:
    return ", ".join(scene.negative_constraints)

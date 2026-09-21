"""Prompt-preview composition from canonical identity plus a resolved take."""

from __future__ import annotations

from engine.scene_models import ResolvedScene
from pools.realism import realism_text


def compose_prompt(scene: ResolvedScene) -> str:
    selection = scene.selections
    activity = f" while {selection['activity']}" if "activity" in selection else ""
    optional = [
        f"hair styled {selection['hair_style']}" if "hair_style" in selection else None,
        f"expression: {selection['expression']}" if "expression" in selection else None,
        f"season: {selection['season']}" if "season" in selection else None,
    ]
    direction = "; ".join(item for item in optional if item)
    realism = realism_text(scene.brief.image_style, framing=selection["framing"])
    identity = "; ".join(scene.identity_anchors)
    prompt = (
        f"Photograph of the established character{activity}. "
        f"Identity anchors: {identity}. "
        f"Scene: {selection['pose']} in a {selection['location']}; "
        f"{selection['wardrobe']}; {selection['lighting']} lighting; "
        f"{selection['atmosphere']} atmosphere; {selection['framing']} framing."
    )
    if direction:
        prompt += f" Direction: {direction}."
    if realism:
        prompt += f" {realism}"
    return prompt


def compose_negative_prompt(scene: ResolvedScene) -> str:
    return ", ".join(scene.negative_constraints)

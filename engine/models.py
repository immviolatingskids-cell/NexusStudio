from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Identity:
    name: str
    age: int
    gender: str
    nationality: str
    home: str
    nickname: str | None = None


@dataclass(frozen=True)
class Occupation:
    primary: str
    route: str | None = None
    focus: tuple[str, ...] = ()


@dataclass(frozen=True)
class Character:
    schema_version: str
    character_id: str

    identity: Identity
    appearance: dict[str, Any]
    occupation: Occupation

    hobbies: tuple[str, ...]
    interests: tuple[str, ...]
    personality: tuple[str, ...]

    affinities: dict[str, int]

    sociality: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Character":
        identity_data = data["identity"]
        occupation_data = data["occupation"]

        identity = Identity(
            name=identity_data["name"],
            nickname=identity_data.get("nickname"),
            age=identity_data["age"],
            gender=identity_data["gender"],
            nationality=identity_data["nationality"],
            home=identity_data["home"],
        )

        occupation = Occupation(
            primary=occupation_data["primary"],
            route=occupation_data.get("route"),
            focus=tuple(occupation_data.get("focus", [])),
        )

        return cls(
            schema_version=str(data["schema_version"]),
            character_id=data["character_id"],
            identity=identity,
            appearance=data["appearance"],
            occupation=occupation,
            hobbies=tuple(data.get("hobbies", [])),
            interests=tuple(data.get("interests", [])),
            personality=tuple(data.get("personality", [])),
            affinities=dict(data.get("affinities", {})),
            sociality=dict(data.get("sociality", {})),
        )
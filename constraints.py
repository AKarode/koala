from enum import IntEnum
from typing import List, Optional
from pydantic import BaseModel


class ConstraintLevel(IntEnum):
    """Hierarchical constraint priorities - lower number = higher priority"""
    FATAL = 0      # Anaphylaxis risk
    MEDICAL = 1    # Celiac, diabetes, alpha-gal
    RELIGIOUS = 2  # Halal, kosher, jain
    PREFERENCE = 3 # Vegan, vegetarian


class ConstraintDefinition(BaseModel):
    key: str
    level: ConstraintLevel
    terms: List[str]
    match_mode: str = "word"  # "word" or "substring"


class ConstraintCatalog:
    def __init__(self, definitions: List[ConstraintDefinition]):
        self._definitions = {d.key: d for d in definitions}

    def get(self, key: str) -> Optional[ConstraintDefinition]:
        return self._definitions.get(key)

    def all(self) -> List[ConstraintDefinition]:
        return list(self._definitions.values())

    def merged(self, custom_definitions: List[ConstraintDefinition]) -> "ConstraintCatalog":
        merged = dict(self._definitions)
        for definition in custom_definitions:
            merged[definition.key] = definition
        return ConstraintCatalog(list(merged.values()))


DEFAULT_CONSTRAINTS = [
    ConstraintDefinition(
        key="peanut",
        level=ConstraintLevel.FATAL,
        terms=["peanut", "peanuts", "groundnut", "arachis", "satay", "praline", "nu cham"],
    ),
    ConstraintDefinition(
        key="shellfish",
        level=ConstraintLevel.FATAL,
        terms=["shrimp", "crab", "lobster", "prawn", "crayfish", "scallop", "oyster", "clam", "mussel"],
    ),
    ConstraintDefinition(
        key="halal",
        level=ConstraintLevel.RELIGIOUS,
        terms=["pork", "bacon", "ham", "lard", "gelatin", "pepperoni", "prosciutto",
               "wine", "alcohol", "beer", "rum", "vanilla extract"],
    ),
    ConstraintDefinition(
        key="celiac",
        level=ConstraintLevel.MEDICAL,
        terms=["wheat", "barley", "rye", "malt", "soy sauce", "couscous",
               "bulgur", "semolina", "spelt", "triticale", "miso"],
    ),
]

DEFAULT_CATALOG = ConstraintCatalog(DEFAULT_CONSTRAINTS)


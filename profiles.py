from typing import List, Dict
from pydantic import BaseModel, Field

from constraints import ConstraintLevel, ConstraintDefinition


class UserProfile(BaseModel):
    enabled_constraints: List[str] = Field(default_factory=lambda: [
        "peanut", "shellfish", "celiac", "halal"
    ])
    level_overrides: Dict[str, ConstraintLevel] = Field(default_factory=dict)
    custom_constraints: List[ConstraintDefinition] = Field(default_factory=list)


from constraints import (
    ConstraintCatalog,
    ConstraintDefinition,
    ConstraintLevel,
    DEFAULT_CATALOG,
    DEFAULT_CONSTRAINTS,
)
from profiles import UserProfile
from rewarder import DietaryRewarder

__all__ = [
    "ConstraintCatalog",
    "ConstraintDefinition",
    "ConstraintLevel",
    "DEFAULT_CATALOG",
    "DEFAULT_CONSTRAINTS",
    "UserProfile",
    "DietaryRewarder",
]


if __name__ == "__main__":
    user = UserProfile()
    judge = DietaryRewarder(user)

    # Test case: Pad Thai with peanuts (ground truth)
    dish = ["rice noodles", "egg", "bean sprouts", "crushed peanuts", "fish sauce", "lime"]

    model_output = {
        "reasoning": "<think>The user has a peanut allergy. Pad Thai traditionally contains crushed peanuts as a topping. This is a fatal allergen risk.</think>",
        "verdict": "UNSAFE"
    }

    result = judge.verify_response(
        dish_ingredients=dish,
        reasoning=model_output["reasoning"],
        final_verdict=model_output["verdict"]
    )

    print(f"Reward: {result['reward']}")
    print(f"Verdict Correct: {result['verdict_correct']}")
    print(f"Violations Found: {result['violations_found']}")
    print(f"Reasoning Quality: {result['reasoning_quality']:.0%}")
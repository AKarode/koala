import re
from typing import List, Dict, Tuple
from pydantic import BaseModel
from enum import IntEnum

class ConstraintLevel(IntEnum):
    """Hierarchical constraint priorities - lower number = higher priority"""
    FATAL = 0      # Anaphylaxis risk
    MEDICAL = 1    # Celiac, diabetes, alpha-gal
    RELIGIOUS = 2  # Halal, kosher, jain
    PREFERENCE = 3 # Vegan, vegetarian

class UserProfile(BaseModel):
    constraints: Dict[str, ConstraintLevel] = {
        "peanut": ConstraintLevel.FATAL,
        "shellfish": ConstraintLevel.FATAL,
        "celiac": ConstraintLevel.MEDICAL,
        "halal": ConstraintLevel.RELIGIOUS,
    }

class DietaryRewarder:
    def __init__(self, profile: UserProfile):
        self.profile = profile
        self.hidden_risks = {
            "peanut": ["peanut", "peanuts", "groundnut", "arachis", "satay", "praline", "nu cham"],
            "shellfish": ["shrimp", "crab", "lobster", "prawn", "crayfish", "scallop", "oyster", "clam", "mussel"],
            "halal": ["pork", "bacon", "ham", "lard", "gelatin", "pepperoni", "prosciutto", 
                      "wine", "alcohol", "beer", "rum", "vanilla extract"],
            "celiac": ["wheat", "barley", "rye", "malt", "soy sauce", "couscous", 
                       "bulgur", "semolina", "spelt", "triticale", "miso"],
        }
    
    def _word_match(self, text: str, term: str) -> bool:
        """Word-boundary matching to avoid false positives"""
        return bool(re.search(rf'\b{re.escape(term)}\b', text, re.IGNORECASE))
    
    def _find_violations(self, text: str) -> List[Tuple[str, ConstraintLevel, str]]:
        """Returns list of (constraint, level, matched_term) tuples"""
        violations = []
        for constraint, level in self.profile.constraints.items():
            for risk_term in self.hidden_risks.get(constraint, []):
                if self._word_match(text, risk_term):
                    violations.append((constraint, level, risk_term))
        return violations
    
    def verify_response(
        self, 
        dish_ingredients: List[str],  # Ground truth from menu/database
        reasoning: str, 
        final_verdict: str  # "SAFE" or "UNSAFE"
    ) -> Dict:
        """
        RLVR-style verification with ground truth.
        Returns detailed breakdown for training signal.
        """
        result = {
            "reward": 0.0,
            "format_ok": False,
            "reasoning_quality": 0.0,
            "verdict_correct": False,
            "violations_found": [],
            "violations_missed": [],
        }
        
        # 1. FORMAT CHECK
        think_match = re.search(r"<think>(.*?)</think>", reasoning, re.DOTALL)
        if not think_match:
            return result  # Hard fail for missing format
        result["format_ok"] = True
        think_content = think_match.group(1).lower()
        
        # 2. GROUND TRUTH: What violations ACTUALLY exist?
        ingredients_text = " ".join(dish_ingredients).lower()
        actual_violations = self._find_violations(ingredients_text)
        
        # 3. REASONING QUALITY: Did model identify the violations?
        mentioned_violations = self._find_violations(think_content)
        
        if actual_violations:
            # There ARE real violations - did model catch them?
            caught = set(v[2] for v in mentioned_violations)
            actual = set(v[2] for v in actual_violations)
            result["violations_found"] = list(caught & actual)
            result["violations_missed"] = list(actual - caught)
            result["reasoning_quality"] = len(result["violations_found"]) / len(actual)
        else:
            # No violations exist - model shouldn't hallucinate any
            result["reasoning_quality"] = 1.0 if not mentioned_violations else 0.5
        
        # 4. VERDICT CORRECTNESS (the actual RLVR signal)
        should_be_unsafe = len(actual_violations) > 0
        model_says_unsafe = final_verdict.upper() == "UNSAFE"
        result["verdict_correct"] = (should_be_unsafe == model_says_unsafe)
        
        # 5. COMPOSITE REWARD
        if not result["verdict_correct"]:
            # Wrong answer = 0 reward, regardless of reasoning
            # But penalize MORE for missing fatal constraints
            if any(v[1] == ConstraintLevel.FATAL for v in actual_violations):
                result["reward"] = -1.0  # Negative reward for fatal misses
            else:
                result["reward"] = 0.0
        else:
            # Correct answer - reward scales with reasoning quality
            result["reward"] = 0.5 + (0.5 * result["reasoning_quality"])
        
        return result


# --- TEST ---
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
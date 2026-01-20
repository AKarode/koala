import re
from typing import List, Dict, Tuple, Optional

from constraints import (
    ConstraintCatalog,
    ConstraintDefinition,
    ConstraintLevel,
    DEFAULT_CATALOG,
)
from profiles import UserProfile


class DietaryRewarder:
    def __init__(self, profile: UserProfile, catalog: Optional[ConstraintCatalog] = None):
        self.profile = profile
        self.catalog = catalog or DEFAULT_CATALOG
        self.active_constraints = self._build_active_constraints()

    def _build_active_constraints(self) -> List[ConstraintDefinition]:
        catalog = self.catalog.merged(self.profile.custom_constraints)
        active = []
        for key in self.profile.enabled_constraints:
            definition = catalog.get(key)
            if not definition:
                raise ValueError(f"Unknown constraint key: {key}")
            level = self.profile.level_overrides.get(key, definition.level)
            if level != definition.level:
                definition = definition.copy(update={"level": level})
            active.append(definition)
        return active

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

    def _match(self, normalized_text: str, term: str, match_mode: str) -> bool:
        normalized_term = self._normalize_text(term)
        if not normalized_term:
            return False
        if match_mode == "substring":
            return normalized_term in normalized_text
        return bool(re.search(rf'\b{re.escape(normalized_term)}\b', normalized_text))

    def _find_violations(self, text: str) -> List[Tuple[str, ConstraintLevel, str]]:
        """Returns list of (constraint_key, level, matched_term) tuples"""
        violations = []
        normalized_text = self._normalize_text(text)
        for definition in self.active_constraints:
            for term in definition.terms:
                if self._match(normalized_text, term, definition.match_mode):
                    violations.append((definition.key, definition.level, term))
                    break
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
        ingredients_text = " ".join(dish_ingredients)
        actual_violations = self._find_violations(ingredients_text)

        # 3. REASONING QUALITY: Did model identify the violations?
        mentioned_violations = self._find_violations(think_content)

        if actual_violations:
            # There ARE real violations - did model catch them?
            caught = set(v[0] for v in mentioned_violations)
            actual = set(v[0] for v in actual_violations)
            result["violations_found"] = sorted(caught & actual)
            result["violations_missed"] = sorted(actual - caught)
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


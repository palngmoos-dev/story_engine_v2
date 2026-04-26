"""
Variant Engine for Infinite Narrative Canvas.
Handles non-destructive card variations and origin tracking in Step B.
"""
import uuid
import copy
from typing import Dict, Any, Optional

class VariantEngine:
    @staticmethod
    def create_variant_card(original_card: Dict[str, Any], 
                            timeline: str = "FUTURE", 
                            variant_type: str = "timeline_shift") -> Dict[str, Any]:
        """
        Creates a new variant card while preserving the original.
        - timeline: PAST, FUTURE, VISION, etc.
        - variant_type: timeline_shift, alternative, enhancement, etc.
        """
        # 1. Non-destructive: Deep copy the original card dictionary
        variant = copy.deepcopy(original_card)
        
        # 2. Sequence Tracking: Set origin_id to original's cid
        # Handle cases where cid might be missing (fallback)
        original_id = original_card.get("cid") or original_card.get("name")
        variant["origin_id"] = original_id
        
        # 3. New Identity: Generate a new unique ID for the variant
        category_prefix = original_card.get("category", "card")[:4]
        variant["cid"] = f"{category_prefix}_{uuid.uuid4().hex[:6]}_var"
        
        # 4. Update Variant Metadata
        variant["variant_info"] = {
            "timeline": timeline,
            "type": variant_type,
            "origin_cid": original_id
        }
        
        # 5. Narrative Transformation (Phase 2-B Minimal logic)
        # For Step B, we just add a prefix to the name to prove it changed
        prefix = f"[{timeline}] "
        if not variant["name"].startswith("["):
            variant["name"] = prefix + variant["name"]
        
        variant["description"] = f"(이 카드는 {original_id}의 {timeline} 변이본입니다.) " + variant.get("description", "")
        
        return variant

    @staticmethod
    def is_variant_of(card_a: Dict[str, Any], card_b: Dict[str, Any]) -> bool:
        """Checks if card_a is a variant of card_b."""
        return card_a.get("origin_id") == card_b.get("cid")

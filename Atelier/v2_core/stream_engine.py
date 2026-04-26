"""
Stream Engine for Infinite Narrative Canvas.
Handles generation and accumulation of card pages in Step B.
"""
import random
from typing import List, Dict, Any
from .state_model import WorldState
from . import card_engine as cards

class StreamEngine:
    @staticmethod
    def generate_stream_page(count: int = 10) -> List[Dict[str, Any]]:
        """
        Generates a page (deck) of cards for the stream.
        Uses a mix of presets and randomized attributes for Step B proof.
        """
        all_presets = cards.get_all_presets()
        categories = list(all_presets.keys())
        page = []
        
        for i in range(count):
            # Pick a random category and a random card name from presets
            cat = random.choice(categories)
            name = random.choice(all_presets[cat])
            
            # Create a simple card dict (to be AI-enhanced in next steps)
            card_item = {
                "name": name,
                "category": cat,
                "description": f"서사의 {cat} 요소를 더욱 풍성하게 만드는 영감의 카드입니다.",
                "origin_id": None,
                "variant_info": {"timeline": "PRESENT", "type": "ORIGINAL"}
            }
            
            # Attempt to pull existing preset impact/details if available
            # This demonstrates integration with the existing Registry
            page.append(card_item)
            
        return page

    @staticmethod
    def append_stream_page(state: WorldState, page: List[Dict[str, Any]]):
        """Appends a new page of cards to the world state's stream history."""
        state.stream_pages.append(page)
        
        # TODO: Implement hybrid compression logic for older pages (N > 20)
        # For Step B, we keep everything to ensure accumulation works.

    @staticmethod
    def get_latest_page(state: WorldState) -> List[Dict[str, Any]]:
        """Returns the most recently generated stream page."""
        if state.stream_pages:
            return state.stream_pages[-1]
        return []

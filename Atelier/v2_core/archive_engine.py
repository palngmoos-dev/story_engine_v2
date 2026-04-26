"""
Archive Engine for Infinite Narrative Canvas.
Handles hybrid compression of old stream pages in Step C.
"""
from typing import List, Dict, Any
from .state_model import WorldState

class ArchiveEngine:
    @staticmethod
    def compress_old_stream_pages(state: WorldState, keep_recent: int = 10) -> int:
        """
        Compresses old stream pages into summary metadata.
        Keeps the latest 'keep_recent' pages intact.
        Returns the number of pages compressed.
        """
        total_pages = len(state.stream_pages)
        if total_pages <= keep_recent:
            return 0
        
        num_to_compress = total_pages - keep_recent
        pages_to_archive = state.stream_pages[:num_to_compress]
        
        # Create summaries for each page to be compressed
        for i, page in enumerate(pages_to_archive):
            card_names = [card.get("name", "Unknown") for card in page]
            categories = list(set([card.get("category", "None") for card in page]))
            
            summary = {
                "original_page_index": i,
                "card_count": len(page),
                "representative_names": card_names[:5], # Keep first 5 names as sample
                "categories": categories,
                "is_compressed": True
            }
            state.compressed_stream_history.append(summary)
            
        # Remove compressed pages from the active stream
        state.stream_pages = state.stream_pages[num_to_compress:]
        
        return num_to_compress

    @staticmethod
    def get_archive_stats(state: WorldState) -> Dict[str, Any]:
        """Returns statistics about current archive/compression state."""
        return {
            "active_pages": len(state.stream_pages),
            "compressed_pages": len(state.compressed_stream_history),
            "total_inspiration_units": len(state.compressed_stream_history) * 10 # Estimated
        }

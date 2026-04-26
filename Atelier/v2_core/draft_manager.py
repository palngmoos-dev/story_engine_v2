import json
import os

DRAFT_FILE = "current_draft.json"

def save_draft(draft_data):
    """
    Saves the current work state to current_draft.json.
    Expected draft_data structure:
    {
        "status": "story_confirmed" | "character_confirmed" | "completed",
        "story": { "genre": "...", "one_liner": "...", "plot": "...", "reason": "..." },
        "character": { "name": "...", "age": "...", ... , "background": "..." }
    }
    """
    try:
        with open(DRAFT_FILE, "w", encoding="utf-8") as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving draft: {e}")
        return False

def load_draft():
    """
    Loads the work state from current_draft.json if it exists.
    Returns None if file not found or error occurs.
    """
    if not os.path.exists(DRAFT_FILE):
        return None
    
    try:
        with open(DRAFT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading draft: {e}")
        return None

def clear_draft():
    """Deletes the current_draft.json file to start fresh."""
    if os.path.exists(DRAFT_FILE):
        os.remove(DRAFT_FILE)

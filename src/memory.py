import json
import os
import datetime
from typing import List, Dict, Optional
from src.config import MEMORY_FILE, TODO_FILE

class MemoryEngine:
    def __init__(self):
        self.file_path = MEMORY_FILE
        self.todo_path = TODO_FILE
        self.memory = self._load_memory()
        self.todos = self._load_todos()

    def _load_todos(self) -> List[Dict]:
        if not os.path.exists(self.todo_path):
            return []
        try:
            with open(self.todo_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_todos(self):
        with open(self.todo_path, 'w', encoding='utf-8') as f:
            json.dump(self.todos, f, indent=4, ensure_ascii=False)

    def add_todo(self, text: str):
        item = {
            "text": text,
            "created_at": str(datetime.datetime.now())
        }
        self.todos.append(item)
        self._save_todos()

    def get_todos(self) -> List[str]:
         return [t["text"] for t in self.todos]

    def clear_todos(self):
        self.todos = []
        self._save_todos()
        
    def remove_todo_by_index(self, idx: int):
        if 0 <= idx < len(self.todos):
            rm = self.todos.pop(idx)
            self._save_todos()
            return rm["text"]
        return None

    def _load_memory(self) -> Dict:
        if not os.path.exists(self.file_path):
            return {"conversations": [], "facts": {}, "preferences": {}}
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"conversations": [], "facts": {}, "preferences": {}}

    def _save_memory(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=4, ensure_ascii=False)

    def get_mood_streak(self, mood_keyword, days=3):
        """Checks backwards interactions for recurrence of a mood."""
        # This is a bit expensive if memory is huge, but for V1 JSON it's fine.
        count = 0
        target = mood_keyword.lower()
        
        # Reverse iterate
        for entry in reversed(self.memory["conversations"]):
            txt = entry["user"].lower()
            if target in txt:
                count += 1
            if count >= days:
                return count
            # Stop if we went back too far (e.g. 50 items) for performance
            # In V3 we assume simple stack check
        
        return count

    def store_fact(self, category: str, content: str, fact_type: str = "observed", confidence: str = "observed"):
        timestamp = datetime.datetime.now().isoformat()
        if category not in self.memory["facts"]:
            self.memory["facts"][category] = []
        
        # Check for duplicates or similar facts? For V6 we just append.
        entry = {
            "content": content, 
            "timestamp": timestamp,
            "type": fact_type,          # factual, emotional, temporary, long-term
            "confidence": confidence    # observed vs confirmed
        }
        self.memory["facts"][category].append(entry)
        self._save_memory()

    def confirm_last_fact(self, category: str):
        """Upgrades the confidence of the last fact in a category."""
        if category in self.memory["facts"] and self.memory["facts"][category]:
             self.memory["facts"][category][-1]["confidence"] = "confirmed"
             self._save_memory()
             return True
        return False
             
    def add_core_fact(self, content: str):
        """Shortcut for adding a confirmed truth."""
        self.store_fact("core", content, fact_type="factual", confidence="confirmed")
    
    def search_facts(self, keyword: str) -> List[str]:
        results = []
        keyword = keyword.lower()
        for category, items in self.memory["facts"].items():
            for item in items:
                if keyword in item["content"].lower():
                    results.append(item["content"])
        return results

    def clear_memory(self):
        self.memory = {"conversations": [], "facts": {}, "preferences": {}}
        self._save_memory()

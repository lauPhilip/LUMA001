import json
import datetime
import time
from pathlib import Path

class LumaOps:
    def __init__(self, knowledge_dir):
        self.knowledge_dir = Path(knowledge_dir)
        self.is_active = False
        self.progress = 0.0
        self.current_op = "IDLE"

    def _load_json(self, filename, default_type=list):
            """Loads JSON with a safety net for empty files."""
            path = self.knowledge_dir / filename
            
            # If the file doesn't exist, start fresh
            if not path.exists():
                return default_type()

            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # If the file is 0 bytes, return the default structure
                    if not content:
                        return default_type()
                    return json.loads(content)
            except (json.JSONDecodeError, ValueError):
                # If the file is corrupted, we reset it to prevent crashes
                print(f"LUMA_LOG: {filename} was corrupted or empty. Resetting.")
                return default_type()

    def _save_json(self, filename, data):
            """Safely saves data to the knowledge folder, creating it if necessary."""
            path = self.knowledge_dir / filename
            
            # FIX: Ensure the parent directory exists before opening the file
            if not self.knowledge_dir.exists():
                print(f"LUMA_LOG: Creating missing directory: {self.knowledge_dir}")
                self.knowledge_dir.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
    
    def write_session_summary(self, last_focus):
        """Finalizes the session and writes to session.json."""
        self.is_active = True
        self.current_op = "SAVING SESSION"
        
        summary = {
            "session_id": datetime.datetime.now().strftime("%Y-%m-%d_S%H"),
            "timestamp": datetime.datetime.now().isoformat(),
            "last_focus": last_focus
        }
        
        self._save_json("session.json", summary) #
        
        self.is_active = False
        return "Session highlights have been indexed, Master Lau."

    def scribe_note(self, content):
            """Appends a new thought to the scribe_log.json."""
            self.is_active = True
            self.current_op = "SCRIBING THOUGHT"
            
            # We ensure it loads as a list even if the file was empty
            data = self._load_json("scribe_log.json", default_type=list)
            
            new_entry = {
                "id": len(data) + 1,
                "timestamp": datetime.datetime.now().isoformat(),
                "content": content
            }
            
            data.append(new_entry)
            self._save_json("scribe_log.json", data) #
            
            self.is_active = False
            return new_entry["id"]

    def archive_to_long_term(self, solution_title, logic_summary):
        """Determinate op: Progress bar (3-10s)."""
        self.is_active = True
        self.current_op = "ARCHIVING"
        
        # Progress simulation for the 'Agentic' feel
        for i in range(1, 11):
            self.progress = i / 10.0
            time.sleep(0.4) 

        data = self._load_json("long_term_memory.json")
        new_sol = {
            "id": f"SOL_{datetime.datetime.now().strftime('%y%m%d_%H%M')}",
            "title": solution_title,
            "content": logic_summary,
            "timestamp": datetime.datetime.now().isoformat()
        }
        # Assuming archived_solutions key exists
        if "archived_solutions" not in data: data["archived_solutions"] = []
        data["archived_solutions"].append(new_sol)
        self._save_json("long_term_memory.json", data)
        
        self.is_active = False
        self.progress = 0.0
        return new_sol["id"]

    def write_project_update(self, content):
        """Saves milestones to projects.json."""
        self.is_active = True
        self.current_op = "UPDATING PROJECTS"
        
        # Load as a list, safety-checked by our new _load_json
        data = self._load_json("projects.json", default_type=list)
        
        new_project_entry = {
            "id": f"PRJ-{len(data) + 101}",
            "timestamp": datetime.datetime.now().isoformat(),
            "details": content
        }
        
        data.append(new_project_entry)
        self._save_json("projects.json", data)
        
        self.is_active = False
        return new_project_entry["id"]
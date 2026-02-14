import psutil
import datetime
import webbrowser
from pathlib import Path

class LumaSkills:
    def __init__(self, luma_instance, ops_instance):
        self.luma = luma_instance
        self.ops = ops_instance 
        
        self.registry = {
            "system vitals": self.telemetry_pulse,
            "cpu load": self.telemetry_pulse,
            "file heartbeat": self.file_heartbeat,
            "search for": self.web_search_dispatch,
            "look up": self.web_search_dispatch,
            "note down": self.contextual_scribe,
            "remember that": self.contextual_scribe,
            "scribe": self.contextual_scribe,
            "archive this": self.archive_logic,
            "update project": self.manage_projects,
            "project milestone": self.manage_projects,
            "new project": self.manage_projects,
            "search memory": self.memory_recall,
            "what did i say about": self.memory_recall,
            "recall note": self.memory_recall
        }

    def classify_intent(self, text):
        """Triage: Engineering focus vs. Daily chatter."""
        tech_keywords = [".py", "fix", "code", "logic", "milestone", "luma-", "error"]
        is_tech = any(kw in text.lower() for kw in tech_keywords)
        return ("CORE", 200) if is_tech else ("SECONDARY", 80)
    
    def memory_recall(self, text):
        """Scans the scribe_log for specific technical keywords."""
        # Strip the trigger to find the search term
        query = text.lower().replace("search memory for", "").replace("recall note about", "").strip()
        
        # Pull the full log from Ops
        notes = self.ops._load_json("scribe_log.json", default_type=list)
        
        # Filter for the query
        matches = [n['content'] for n in notes if query in n['content'].lower()]
        
        if matches:
            # Return the most recent match to keep it concise
            return f"I've found a match in my archives: '{matches[-1]}'. Does that help, Lau?"
        return f"I've scanned the scribe logs, but I can't find anything related to '{query}'."
    
    def manage_projects(self, text):
        """Directly writes to projects.json."""
        # Logic to extract project name and detail from text
        # Example: "update project LUMA-ORB milestone 1 complete"
        clean_text = text.lower().replace("update project", "").strip()
        
        # This calls a new method we'll add to LumaOps
        project_id = self.ops.write_project_update(clean_text) 
        return f"Project telemetry updated, Lau. Reference ID: {project_id}."

    def telemetry_pulse(self, text=None):
        cpu = psutil.cpu_percent() #
        return f"CPU is holding at {cpu} percent, Master Lau."

    def contextual_scribe(self, text):
        """Direct write to scribe_log.json via Ops."""
        for trigger in ["note down", "remember that", "scribe","write","note"]:
            if trigger in text.lower():
                text = text.lower().split(trigger)[-1].strip()
        
        note_id = self.ops.scribe_note(text) #
        return f"Thought indexed, Lau. Scribe Entry {note_id} is secured."

    def file_heartbeat(self, text):
        """Checks file activity for engineering projects."""
        words = text.split()
        target = next((w for w in words if "." in w), None)
        if target and Path(target).exists():
            mtime = datetime.datetime.fromtimestamp(Path(target).stat().st_mtime)
            return f"The heartbeat for {target} was last seen at {mtime.strftime('%H:%M')}."
        return "I can't find a file heartbeat for that specific target."

    def web_search_dispatch(self, text):
        query = text.lower().replace("search for", "").replace("look up", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"Opening an uplink for '{query}' now."

    def archive_logic(self, text):
        sol_id = self.ops.archive_to_long_term("Manual Archive", self.luma.response_text)
        return f"Logic promoted to archive. ID: {sol_id}."

    def save_session_summary(self, conversation_history):
        last_msg = conversation_history[-1] if conversation_history else "No activity."
        return self.ops.write_session_summary(last_msg)
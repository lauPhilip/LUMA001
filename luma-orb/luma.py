# luma.py - V2 Cognitive Core with Markdown Grounding
import requests
import threading
import time
from pathlib import Path
from luma_skills import LumaSkills
from luma_ops import LumaOps

class Luma:
    def __init__(self, cfg):
        self.cfg = cfg
        self.voice_engine = None
        self.is_thinking = False
        self.current_mode = "STANDARD"
        self.response_text = "L.U.M.A. V2 'Whisper-Grade' Online. Awaiting input."
        self.knowledge_dir = Path("knowledge")
        self.ops = LumaOps(knowledge_dir=self.knowledge_dir)
        self.skills = LumaSkills(self, self.ops)
        
        # Initialize knowledge containers
        self.persona_md = ""
        self.guardrails_md = ""
        self.long_term_md = ""
        self.user = {}
        self.projects = []
        self.session = []
        
        self.refresh_knowledge() # Initial load

    def _load_md(self, filename):
        """Helper to read Markdown files safely."""
        path = self.knowledge_dir / filename
        return path.read_text(encoding='utf-8') if path.exists() else ""

    def refresh_knowledge(self):
            """Uplink to the full hybrid Knowledge Deck (MD focus)."""
            # Load Identity & Rules (Markdown)
            self.persona_md = self._load_md("persona.md")
            self.guardrails_md = self._load_md("guardrails.md")
            self.long_term_md = self._load_md("long_term_memory.md")
            # NEW: Load user profile from Markdown
            self.user_md = self._load_md("user.md") 
            
            # Keep dynamic lists as JSON for now
            self.projects = self.ops._load_json("projects.json", default_type=list)
            self.session = self.ops._load_json("session.json", default_type=list)
        
    def startup_briefing(self):
            """Constructs a greeting using the new user.md grounding."""
            self.refresh_knowledge() 
            
            # Simplified logic: the LLM will now read user_md directly in the prompt
            latest_project = self.projects[-1]['project_name'] if self.projects else "the hub"
            
            # Construct the briefing [cite: 2026-02-10]
            briefing = (
                f"Powering up, Master Lau. I've read the latest user logs for the Herning station. "
                f"Archives are synced, and I'm ready to push forward on {latest_project}. "
                "Neural cache is primed—what's the first move?"
            )
            
            if self.voice_engine:
                self.voice_engine.speak(briefing)

    def receive_input(self, text, method="voice"):
        print(f"LUMA_LOG: Processing input: {text} ({method})")
        
        # 1. Skill Check (Fast Path)
        skill_found = False
        for trigger, skill_func in self.skills.registry.items():
            if trigger in text.lower():
                response = skill_func(text)
                self._dispatch_feedback(response, is_quiet=(method=="chat"))
                skill_found = True
                break
        
        # 2. LLM Generation (Slow Path)
        if not skill_found:
            tokens = 60 if self.current_mode == "DEEPWORK" else 150
            threading.Thread(target=self._generate_response, 
                             args=(text, tokens, method=="chat"), daemon=True).start()

    def _generate_response(self, text, tokens, is_quiet):
        self.is_thinking = True
        self.refresh_knowledge() 

        # 1. SAFE HISTORY EXTRACTION
        # We ensure session is a list and take the last 3 entries safely.
        recent_history = list(self.session)[-3:] if self.session else []
        history_str = "\n".join([f"U: {m.get('u')} | L: {m.get('l')}" for m in recent_history])

        # 2. UPDATED AGENTIC PROMPT
        extensive_prompt = f"""
        {self.persona_md}
        
        --- STATION CONTEXT ---
        USER: {self.user.get('name', 'Master Lau')} | ROLE: {self.user.get('role', 'Lead Engineer')}
        MODE: {self.current_mode}
        {self.guardrails_md}
        
        --- MEMORY & PROJECTS ---
        {self.long_term_md}
        ACTIVE PROJECT: {str(self.projects[-1]) if self.projects else "Herning Hub Initialization"}
        
        --- RECENT CONTEXT ---
        {history_str}
        """

        payload = {
            "model": self.cfg.local_model,
            # Pre-filling 'I' forces first-person persona
            "prompt": f"<|system|>\n{extensive_prompt}<|end|>\n<|user|>\n{text}<|end|>\n<|assistant|>\nI",
            "stream": False,
            "options": {"num_predict": tokens, "temperature": 0.7, "top_p": 0.9}
        }

        try:
            print("LUMA_LOG: Sending to Ollama...")
            res = requests.post(self.cfg.ollama_url, json=payload, timeout=20)
            if res.status_code == 200:
                # We must prepend 'I' back to the response since we pre-filled it
                full_reply = "I " + res.json().get('response', '').strip()
                
                # Auto-log to session
                self.ops.modify_knowledge("session.json", {"u": text, "l": full_reply}, mode="append")
                self._dispatch_feedback(full_reply, is_quiet)
            else:
                self._dispatch_feedback("Cognitive uplink failed. Check Ollama.", is_quiet)
        except Exception as e:
            print(f"LUMA_LOG: LLM Error: {e}")
            self._dispatch_feedback("My connection to the neural net is unstable.", is_quiet)
        finally:
            self.is_thinking = False

    def _dispatch_feedback(self, text, is_quiet):
        self.response_text = text
        if not is_quiet and self.voice_engine:
            self.voice_engine.speak(text)
import json
from groq import Groq
from config import Config

class Brain:
    def __init__(self):
        if Config.GROQ_API_KEY:
            self.client = Groq(api_key=Config.GROQ_API_KEY)
        else:
            self.client = None

    def analyze(self, company, text):
        if not self.client: return {"status": "QUALIFIED", "hook": "manual mode"}
        
        prompt = f"""
        Analyze this audio studio website for '{company}'.
        EXTRACT:
        1. TECH HOOK: A specific piece of high-end gear (console, mic, plugin) or a major credit (Netflix, HBO).
        2. SEGMENT: 'Post-Production', 'Music', 'Audiobook'.
        
        TEXT: {text[:3000]}
        
        JSON OUTPUT: {{ "hook": "...", "segment": "..." }}
        """
        
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except:
            return {"hook": "professional audio services", "segment": "Studio"}

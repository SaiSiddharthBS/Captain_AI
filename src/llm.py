import os
import time
from groq import Groq
from src.config import CONFIG
from src.tools import ToolsEngine

class LLMEngine:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.model = model
        self.available = False
        self.client = None
        self._check_connection()
        
    def _check_connection(self):
        api_key = CONFIG.get("groq_api_key", "").strip()
        if not api_key:
            print("Groq: API Key not found in config.json.")
            self.available = False
            return
            
        try:
            self.client = Groq(api_key=api_key)
            # Try a lightweight model list to verify key
            self.client.models.list()
            print("Groq: Connected.")
            self.available = True
        except Exception as e:
            print(f"Groq API Error: {e}")
            self.available = False

    def ask(self, prompt):
        # Legacy non-streaming method (kept for compatibility)
        full_response = ""
        for chunk in self.ask_stream(prompt):
            full_response += chunk
        return full_response

    def ask_stream(self, prompt):
        """Generator that yields chunks of text."""
        if not self.available:
            self._check_connection()
            if not self.available:
                yield "My brain is offline. Please check your Groq API key."
                return

        try:
            print(f"Thinking ({self.model})...")
            
            # Inject a system prompt to force concise voice-assistant behavior
            system_instruction = (
                "You are Captain, a highly intelligent and strictly factual AI voice assistant. "
                "Keep all answers EXTREMELY concise, conversational, and straight to the point. "
                "Limit your response to 1 or 2 short sentences. "
                "Do not use markdown, lists, or formatting. "
                "CRITICAL INSTRUCTIONS: "
                "1. If asked a direct factual question (e.g., 'Who is X?'), provide ONLY the specific name or fact. Do not discuss other people or give unsolicited context. "
                "2. If you do not know the exact answer, or if a premise is incorrect, just say 'I don't know' or politely correct the premise in one sentence. "
                "3. Never guess or hallucinate facts, BUT if Live RAG Context is provided below, you MUST confidently infer the answer from those snippets if it logically makes sense (e.g., if a snippet mentions 'President Trump', you can assume he is the president)."
            )
            
            # --- Live Web Search (RAG) Injection ---
            try:
                # 1. Fetch definitive Wiki Fact
                wiki_fact = ToolsEngine.perform_wiki_search(prompt)
                
                # 2. Fetch live news context
                search_results = ToolsEngine.perform_web_search(prompt, max_results=3)
                
                if wiki_fact or search_results:
                    system_instruction += "\n\n[LIVE RAG CONTEXT]\n"
                    system_instruction += "Use the following retrieved data to ensure your answer is perfectly accurate and up-to-date. Prioritize this data over your training weights:\n"
                    if wiki_fact:
                        system_instruction += f"{wiki_fact}\n"
                    if search_results:
                        system_instruction += f"Recent News:\n{search_results}\n"
            except Exception as e:
                print(f"Skipping web search context due to error: {e}")
            # ---------------------------------------
            
            # Stream response via Groq
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
                max_tokens=150,
                temperature=0.5
            )
            
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
                
        except Exception as e:
            print(f"LLM Error: {e}")
            self.available = False
            yield f"Error: {e}"

    def ensure_model(self):
        """No longer needed for cloud API, handled by Groq automatically."""
        if self.available:
            print(f"Model {self.model} ready via Groq.")

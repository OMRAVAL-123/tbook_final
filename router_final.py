
import os
import pathlib
import sys
import importlib.util
import sqlite3
import json

from langchain_groq import ChatGroq

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_ROUTER = "llama-3.3-70b-versatile"
MODEL_MERGER = "llama-3.3-70b-versatile"

class MegaRouter:
    def __init__(self):
        self.root = pathlib.Path(__file__).parent
        self.kb_folders = [d for d in self.root.iterdir() if d.is_dir() and d.name.endswith("_kb")]
        self.kb_summaries = self._load_all_summaries()
        self.router_llm = ChatGroq(model_name=MODEL_ROUTER, temperature=0, groq_api_key=GROQ_API_KEY)
        self.merger_llm = ChatGroq(model_name=MODEL_MERGER, temperature=0.3, groq_api_key=GROQ_API_KEY)

    def _load_all_summaries(self):
        summaries = {}
        for folder in self.kb_folders:
            summ_db = folder / "summaries.db"
            if summ_db.exists():
                try:
                    conn = sqlite3.connect(summ_db)
                    cur = conn.cursor()
                    cur.execute("SELECT chapter_title, summary FROM summaries")
                    rows = cur.fetchall()
                    kb_summ_text = "\n".join([f"- {r[0]}: {r[1]}" for r in rows[:5]]) # Limit just in case
                    summaries[folder.name] = kb_summ_text
                    conn.close()
                except Exception as e:
                    print(f"Error loading summary for {folder.name}: {e}")
                    summaries[folder.name] = "No summary available."
            else:
                summaries[folder.name] = "No summary db found."
        return summaries

    def route_query(self, query):
        context = ""
        for kb, summary in self.kb_summaries.items():
            context += f"KB: {kb}\nSummary: {summary}\n\n"
            
        prompt = f"""You are a routing expert.
Context:
{context}

User Query: "{query}"

Task: Select the most relevant KBs. Return a JSON list of folder names.
Example: ["m_11_kb", "p_12_kb"]
"""
        response = self.router_llm.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.strip("`").replace("json", "").strip()
        try:
            return json.loads(content)
        except:
            # Fallback regex?
            import re
            match = re.search(r'\[.*\]', content)
            if match:
                return json.loads(match.group(0))
            return []

    def call_retriever(self, kb_name, query):
        kb_path = self.root / kb_name
        retriever_file = kb_path / "retriever.py"
        
        if not retriever_file.exists():
            return f"Error: No retriever found for {kb_name}"
            
        # Dynamic import
        spec = importlib.util.spec_from_file_location(f"retriever_{kb_name}", retriever_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"retriever_{kb_name}"] = module
        spec.loader.exec_module(module)
        
        if hasattr(module, 'retrieve'):
            return module.retrieve(query)
        else:
            # Maybe class based? Inspect file I generated.
            # I generated: def retrieve(query): r = Retriever(); return r.retrieve(query)
            # But wait, did I modify the file content correctly?
            # I forgot to put the class inside the string in previous step? No I did RETRIEVER_CODE = r'''...'''
            # But I need to ensure the indented function is correct.
            # In my previous step, I defined: 
            # def retrieve(query):
            #     r = Retriever()
            #     return r.retrieve(query)
            # This is at module level. Let's check indentation in a moment.
            pass
            
        # Instantiate class if needed? 
        if hasattr(module, 'Retriever'):
            r = module.Retriever()
            return r.retrieve(query)
            
        return "Error: retrieve function not found."

    def process(self, query):
        print(f"User Query: {query}")
        
        # 1. Route
        target_kbs = self.route_query(query)
        print(f"------------------------------------\nROUTER SELECTED KBs:\n{target_kbs}\n------------------------------------")
        
        responses = []
        full_responses_text = ""
        
        if not target_kbs:
            print("No KBs selected.")
            return

        for kb in target_kbs:
            if kb not in [k.name for k in self.kb_folders]:
                print(f"Skipping invalid KB: {kb}")
                continue
                
            print(f"Calling {kb}...")
            resp = self.call_retriever(kb, query)
            
            # Formatting
            answer_text = resp.get("answer", "No answer")
            formatted_resp = f"=== RESPONSE FROM {kb} ===\n{answer_text}\n"
            print(formatted_resp)
            
            responses.append(formatted_resp)
            full_responses_text += formatted_resp + "\n"

        # 2. Merge
        print("------------------------------------\nFINAL MERGING\n------------------------------------")
        prompt = f"""You are an expert editor.
User Query: {query}

Responses from Knowledge Bases:
{full_responses_text}

Task:
1. Combine the information into a single coherent answer.
2. Remove redundancy.
3. Preserve mathematical formatting (LaTeX).
4. Structure with clear sections.
5. If listing, present a clean table or list.
"""
        final_answer = self.merger_llm.invoke(prompt)
        
        print("------------------------------------\nFINAL STRUCTURED ANSWER\n------------------------------------")
        print(final_answer.content)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str, help="User query")
    args = parser.parse_args()
    
    router = MegaRouter()
    router.process(args.query)

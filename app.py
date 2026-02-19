
import streamlit as st
import os
import pathlib
import sys
import importlib.util
import sqlite3
import json
import time

from langchain_groq import ChatGroq
from langchain_community.callbacks.manager import get_openai_callback

# Configuration
# Ensure GROQ_API_KEY is detected or ask user
if "GROQ_API_KEY" not in st.session_state:
    st.session_state["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "")

st.set_page_config(page_title="Deep Knowledge Router", layout="wide")

st.title("📚 Intelligent Multi-KB RAG System")

# Sidebar for Key
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Groq API Key", value=st.session_state["GROQ_API_KEY"], type="password")
    if api_key:
        st.session_state["GROQ_API_KEY"] = api_key
        os.environ["GROQ_API_KEY"] = api_key
    
    st.markdown("---")
    st.markdown("**Detected KBs:**")
    
    # Scan for KBs
    base_path = pathlib.Path(__file__).parent
    kb_folders = [d for d in base_path.iterdir() if d.is_dir() and d.name.endswith("_kb")]
    for kb in kb_folders:
        st.code(kb.name)

if not st.session_state["GROQ_API_KEY"]:
    st.warning("Please enter your Groq API Key to continue.")
    st.stop()

# Models
MODEL_ROUTER = "llama-3.3-70b-versatile"
MODEL_MERGER = "llama-3.3-70b-versatile"

class MegaRouterApp:
    def __init__(self):
        self.root = pathlib.Path(__file__).parent
        self.kb_folders = [d for d in self.root.iterdir() if d.is_dir() and d.name.endswith("_kb")]
        self.kb_summaries = self._load_all_summaries()
        self.router_llm = ChatGroq(model_name=MODEL_ROUTER, temperature=0, groq_api_key=st.session_state["GROQ_API_KEY"])
        self.merger_llm = ChatGroq(model_name=MODEL_MERGER, temperature=0.3, groq_api_key=st.session_state["GROQ_API_KEY"])

    def _load_all_summaries(self):
        summaries = {}
        for folder in self.kb_folders:
            summ_txt = folder / "summaries.txt"
            if summ_txt.exists():
                try:
                    with open(summ_txt, "r", encoding="utf-8") as f:
                        # Read first 500 chars as summary preview
                        content = f.read()
                        preview = content[:1000] + "..." if len(content) > 1000 else content
                        summaries[folder.name] = preview
                except Exception as e:
                    summaries[folder.name] = "No summary available."
            else:
                summaries[folder.name] = "No summary txt found."
        return summaries

    def route_query(self, query):
        context = ""
        for kb, summary in self.kb_summaries.items():
            context += f"KB Folder: {kb}\nSummary: {summary}\n\n"
            
        prompt = f"""You are a routing expert.
Context:
{context}

User Query: "{query}"

Task: Select the most relevant KBs.
Rules:
1. Map subjects carefully: 
   - Physics 11 -> p_11_kb, Physics 12 -> p_12_kb
   - Math 11 -> m_11_kb, Math 12 -> m_12_kb
   - Chemistry 11 -> c_11_kb, Chemistry 12 -> c_12_kb
2. If query specifies "Physics 12", ONLY select "p_12_kb".
3. Return a JSON list of folder names.
Example: ["p_12_kb"]
"""
        response = self.router_llm.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.strip("`").replace("json", "").strip()
        try:
            return json.loads(content), response.response_metadata
        except:
            import re
            match = re.search(r'\[.*\]', content)
            if match:
                return json.loads(match.group(0)), response.response_metadata
            return [], response.response_metadata

    def call_retriever(self, kb_name, query):
        kb_path = self.root / kb_name
        retriever_file = kb_path / "retriever.py"
        
        if not retriever_file.exists():
            return {"answer": f"Error: No retriever found for {kb_name}"}
            
        # Dynamic import
        spec = importlib.util.spec_from_file_location(f"retriever_{kb_name}", retriever_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"retriever_{kb_name}"] = module
        spec.loader.exec_module(module)
        
        try:
            if hasattr(module, 'retrieve'):
                return module.retrieve(query)
            else:
                return {"answer": f"Error: retrieve() not found in {kb_name}"}
        except Exception as e:
            return {"answer": f"Error calling retriever: {str(e)}"}

    def merge_answers(self, query, responses_text, intents):
        is_structured = any(i in ["structured", "listing"] for i in intents)
        
        if is_structured:
            prompt = f"""You are a Precise Data Aggregator.
User Query: {query}

Responses from Knowledge Bases:
{responses_text}

Task:
1. Aggregate the provided structured data.
2. Ensure NO numerical/structured data is lost.
3. Do NOT summarize. Concatenate list items/tables strictly.
4. If the data is JSON, keep it valid or present as a markdown table.
5. If the text says "Exact structured match not found", propagate that message.
"""
        else:
            prompt = f"""You are a precise Knowledge Integrator.
User Query: {query}

Responses from various Knowledge Bases:
{responses_text}

Task:
1. Combine the responses into a single coherent and comprehensive answer.
2. If multiple KBs provided information, synthesize them logically.
3. Preserve all mathematical formatting (LaTeX).
4. If ALL responses from KBs indicate the query is out of context or not found, reply ONLY with: "Sorry, the requested information is not available in our knowledge base. It is out of context."
5. Do NOT add information from your own general knowledge that is not present in the provided responses.
6. If the responses contain "Sorry, out of context", ignore those parts and focus on the valid information. If NO valid information is found, see Rule 4.
"""
        response = self.merger_llm.invoke(prompt)
        return response.content, response.response_metadata


# UI Logic
query_input = st.text_input("Ask a question (or multiple, separated by '?'):", placeholder="Explain derivatives? What is integration?")

if st.button("Search") and query_input:
    app = MegaRouterApp()
    
    # Split queries by '?' and clean up
    queries = [q.strip() for q in query_input.split('?') if q.strip()]
    
    st.write(f"Detected {len(queries)} questions.")
    
    for i, query in enumerate(queries):
        st.markdown(f"---")
        st.markdown(f"## ❓ Question {i+1}: {query}")
        
        st.markdown("### 1️⃣ Routing")
        with st.spinner(f"Routing Q{i+1}..."):
            target_kbs, route_meta = app.route_query(query)
            
        st.success(f"Selected KBs: **{target_kbs}**")
        if 'token_usage' in route_meta:
            st.caption(f"Routing Tokens: {route_meta['token_usage']}")
        
        if not target_kbs:
            st.error("No relevant KBs found.")
        else:
            st.markdown("### 2️⃣ Retrieval")
            kb_responses = []
            full_text = ""
            collected_intents = []
            
            cols = st.columns(len(target_kbs))
            
            for idx, kb in enumerate(target_kbs):
                with cols[idx]:
                    st.info(f"Querying {kb}...")
                    resp = app.call_retriever(kb, query)
                    
                    if isinstance(resp, dict):
                        answer = resp.get("answer", "No answer")
                        intent = resp.get("intent", "explanation")
                    else:
                        answer = str(resp)
                        intent = "explanation"
                        
                    collected_intents.append(intent)
                    kb_responses.append(answer)
                    full_text += f"=== RESPONSE FROM {kb} (Intent: {intent}) ===\n{answer}\n\n"
                    
                    with st.expander(f"See Raw Answer from {kb}"):
                        st.markdown(answer)
                        st.json(resp) 
            
            st.markdown("### 3️⃣ Final Answer")
            with st.spinner("Synthesizing final response..."):
                final_ans, merge_meta = app.merge_answers(query, full_text, collected_intents)
                
            st.markdown(final_ans)
            
            if 'token_usage' in merge_meta:
                st.caption(f"Merge Tokens: {merge_meta['token_usage']}")


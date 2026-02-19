
import os
import pathlib

RETRIEVER_CODE = r'''import sqlite3
import pathlib
import os
import re
import json
import warnings
from typing import List, Dict, Any, Tuple

# LangChian & Groq
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Cross Encoder
from sentence_transformers import CrossEncoder

# Suppress warnings
warnings.filterwarnings("ignore")

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_FAST = "llama-3.1-8b-instant"
MODEL_SMART = "llama-3.3-70b-versatile"

class Retriever:
    def __init__(self):
        self.base_path = pathlib.Path(__file__).parent
        self.dbs = list(self.base_path.glob("*.db"))
        self.db_schemas = self._load_schemas()
        
        self.llm_fast = ChatGroq(model_name=MODEL_FAST, temperature=0, groq_api_key=GROQ_API_KEY)
        self.llm_smart = ChatGroq(model_name=MODEL_SMART, temperature=0.3, groq_api_key=GROQ_API_KEY)
        
        # Load FAISS
        self.embeddings = HuggingFaceEmbeddings(
            model_name="thenlper/gte-small",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        try:
            self.vectorstore = FAISS.load_local(
                str(self.base_path), 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            self.retriever_engine = self.vectorstore.as_retriever(search_kwargs={"k": 10})
        except Exception as e:
            print(f"Warning: Could not load FAISS index in {self.base_path}: {e}")
            self.vectorstore = None

        # Cross Encoder
        try:
            self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        except Exception as e:
            print(f"Warning: Could not load CrossEncoder: {e}")
            self.cross_encoder = None

    def _load_schemas(self) -> Dict[str, str]:
        """Dynamically load schemas from all detected sqlite databases."""
        schemas = {}
        for db_path in self.dbs:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                db_schema_str = []
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    col_str = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
                    db_schema_str.append(f"Table: {table_name}\nColumns: {col_str}")
                    
                    # Store mapping of table to db_file for later execution
                    # We assume unique table names across KBs usually, or we clarify in prompt
                
                schemas[db_path.name] = "\n".join(db_schema_str)
                conn.close()
            except Exception as e:
                print(f"Error loading schema for {db_path}: {e}")
        return schemas

    def _detect_intent(self, query: str) -> str:
        query_lower = query.lower()
        listing_keywords = ["list examples", "list problems", "show exercises", "give topics"]
        explanation_keywords = ["explain", "derive", "why", "prove", "how"]
        
        for k in listing_keywords:
            if k in query_lower:
                return "listing"
        
        for k in explanation_keywords:
            if k in query_lower:
                return "explanation"
                
        # Fallback based on structure? Default to explanation if vague?
        # Re-check formula based?
        return "explanation"

    def _generate_sql(self, query: str) -> Dict[str, Any]:
        """Use LLM to generate SQL based on query and schemas."""
        # Collapse all schemas into one context
        full_schema_context = ""
        for db_file, schema in self.db_schemas.items():
            full_schema_context += f"Database File: {db_file}\n{schema}\n\n"
            
        prompt = f"""You are a SQL expert. 
Context:
{full_schema_context}

User Query: "{query}"

Task:
1. Identify the most relevant Database File and Table.
2. Write a SQLite query to answer the user's request.
3. Return ONLY a JSON object with keys: "db_file", "sql_query".
4. Do not start with ```json. Just the raw JSON.
"""
        response = self.llm_fast.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.strip("`").replace("json", "").strip()
        
        try:
            return json.loads(content)
        except:
            # Fallback parsing
            return {}

    def _execute_sql(self, db_file: str, sql_query: str) -> List[Any]:
        db_path = self.base_path / db_file
        if not db_path.exists():
            return [f"Error: Database {db_file} not found."]
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            return [f"Error executing SQL: {e}"]

    def _retrieve_and_rank(self, query: str) -> str:
        if not self.vectorstore:
            return "Error: Vectorstore not initialized."
            
        # 1. FAISS Search
        docs = self.retriever_engine.invoke(query)
        doc_texts = [d.page_content for d in docs]
        
        if not doc_texts:
            return "No relevant context found."

        # 2. Cross Encoder Re-ranking
        if self.cross_encoder:
            pairs = [[query, doc] for doc in doc_texts]
            scores = self.cross_encoder.predict(pairs)
            # Sort by score
            scored_docs = sorted(zip(doc_texts, scores), key=lambda x: x[1], reverse=True)
            top_docs = [d[0] for d in scored_docs[:5]] # Top 5
        else:
            top_docs = doc_texts[:5]
            
        context = "\n\n".join(top_docs)
        
        # 3. LLM Generation
        prompt = f"""You are an expert tutor.
Context:
{context}

Question: {query}

Instructions:
- Explain clearly.
- Use LaTeX for math: inline $...$, display $$...$$.
- If deriving, show steps.
"""
        response = self.llm_smart.invoke(prompt)
        return response.content

    def retrieve(self, query: str) -> Dict[str, Any]:
        intent = self._detect_intent(query)
        kb_name = self.base_path.name
        
        result = {
            "kb": kb_name,
            "intent": intent,
            "chapters_used": [], # Placeholder, could parse from metadata if available
            "answer": ""
        }
        
        if intent == "listing":
            sql_plan = self._generate_sql(query)
            if sql_plan and "db_file" in sql_plan and "sql_query" in sql_plan:
                rows = self._execute_sql(sql_plan["db_file"], sql_plan["sql_query"])
                result["answer"] = str(rows) # Return data as string representation
            else:
                result["answer"] = "Could not generate valid SQL for listing."
                
        else: # explanation
            result["answer"] = self._retrieve_and_rank(query)
            
        return result

# Expose function
def retrieve(query):
    r = Retriever()
    return r.retrieve(query)
'''

def deploy():
    root = pathlib.Path(r"d:\tbook_final")
    kb_folders = [d for d in root.iterdir() if d.is_dir() and d.name.endswith("_kb")]
    
    print(f"Deploying retriever.py to: {[d.name for d in kb_folders]}")
    
    for folder in kb_folders:
        retriever_path = folder / "retriever.py"
        with open(retriever_path, "w", encoding="utf-8") as f:
            f.write(RETRIEVER_CODE)
        print(f"Written {retriever_path}")

if __name__ == "__main__":
    deploy()

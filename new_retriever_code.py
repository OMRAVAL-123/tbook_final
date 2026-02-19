import sqlite3
import pathlib
import os
import re
import json
import warnings
from typing import List, Dict, Any, Tuple

# LangChain & Groq
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
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
        except Exception:
            self.vectorstore = None

        # Cross Encoder
        try:
            self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        except Exception:
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
                    # Skip internal tables
                    if table_name.startswith("sqlite_"): continue
                    
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    col_str = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
                    
                    # Add sample data to help LLM understand format
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                        rows = cursor.fetchall()
                        sample_str = f"Sample rows: {str(rows)}"
                    except:
                        sample_str = "No samples available."
                        
                    db_schema_str.append(f"Table: {table_name}\nColumns: {col_str}\n{sample_str}")
                
                if db_schema_str:
                    schemas[db_path.name] = "\n\n".join(db_schema_str)
                conn.close()
            except Exception as e:
                print(f"Error loading schema for {db_path}: {e}")
        return schemas

    def _detect_intent(self, query: str) -> str:
        query_lower = query.lower()
        
        # 1. Structured Query Detection (Rule 1)
        structured_keywords = ["chapter", "example", "problem", "exercise", "section"]
        listing_keywords = ["list all topics", "list summaries", "all chapters", "list examples", "list exercises"]
        
        # Check listing first as specific subtype of structured
        for k in listing_keywords:
            if k in query_lower:
                return "listing"
                
        # Numeric pattern check (X.Y)
        if re.search(r"\b\d+\.\d+\b", query):
            return "structured"

        for k in structured_keywords:
             if k in query_lower:
                 return "structured"

        # 2. Conceptual/Theoretical (Rule 4)
        conceptual_keywords = ["what is", "explain", "derive", "calculate", "how"]
        for k in conceptual_keywords:
            if k in query_lower:
                return "explanation"
                
        return "explanation"

    def _generate_sql_strict(self, query: str, intent: str) -> Dict[str, Any]:
        """Strict SQL generation for structured queries."""
        # Collapse schemas
        full_schema_context = ""
        for db_file, schema in self.db_schemas.items():
            full_schema_context += f"Database File: {db_file}\n{schema}\n\n"
            
        system_instruction = """You are a Strict SQL Generator.
Rules:
1. ONLY generate SQL for the provided SQLite schemas.
2. For structured queries (e.g., "Chapter 7 Example 2"), you MUST use EXACT MATCHING on columns like 'chapter_name', 'example_id', 'q_id', etc.
3. Do NOT approximate numbers. If user asks for '7.2', query for '7.2' exactly (or LIKE '7.2%'). Do not query for '1.2'.
4. Do NOT use vector search or semantic similarity. Rely purely on SQL WHERE clauses.
5. If the user asks to LIST items, select all relevant rows.
6. Return a JSON object with keys: "db_file", "sql_query".
7. If no relevant table is found, return empty JSON."""

        prompt = f"""{system_instruction}
        
Context Schemas:
{full_schema_context}

User Query: "{query}"

Response (JSON):
"""
        response = self.llm_fast.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.strip("`").replace("json", "").strip()
        try:
            return json.loads(content)
        except:
            return {}

    def _execute_sql(self, db_file: str, sql_query: str) -> List[Any]:
        db_path = self.base_path / db_file
        if not db_path.exists():
            return []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row # Return dict-like rows
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            output = [dict(row) for row in rows]
            conn.close()
            return output
        except Exception as e:
            return [f"SQL Error: {e}"]

    def _retrieve_and_rank(self, query: str) -> str:
        if not self.vectorstore:
            return "Error: Vectorstore not initialized."
        try:
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
                top_docs = [d[0] for d in scored_docs[:5]] 
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
- If relevant information is found in the chunks, use your logic to respond and correct incorrect/incomplete messages.
- If the question is ENTIRELY out of context, reply with: "Sorry, out of context".
"""
            response = self.llm_smart.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error in semantic retrieval: {e}"

    def retrieve(self, query: str) -> Dict[str, Any]:
        intent = self._detect_intent(query)
        kb_name = self.base_path.name
        
        result = {
            "kb": kb_name,
            "intent": intent,
            "answer": ""
        }
        
        if intent in ["structured", "listing"]:
            # Rule 2: Do NOT rely on semantic similarity.
            sql_plan = self._generate_sql_strict(query, intent)
            
            if sql_plan and "db_file" in sql_plan and "sql_query" in sql_plan:
                rows = self._execute_sql(sql_plan["db_file"], sql_plan["sql_query"])
                if rows:
                    # Format output based on intent
                    if intent == "listing":
                        # Rule 3: Return structured bullet format.
                        formatted_rows = "\n".join([f"- {str(row)}" for row in rows])
                        result["answer"] = f"**Found {len(rows)} items:**\n\n{formatted_rows}"
                    else:
                        # Structured match found
                        # Just return the structured data clearly
                        json_str = json.dumps(rows, indent=2)
                        result["answer"] = f"**Strict Match Found:**\n\n```json\n{json_str}\n```"
                else:
                    # Rule 2: If exact match is not present... respond specific msg
                    result["answer"] = "Exact structured match not found in retrieved context."
            else:
                result["answer"] = "Exact structured match not found in retrieved context."
                
        else: # explanation
            # Rule 4: Semantic retrieval is allowed.
            result["answer"] = self._retrieve_and_rank(query)
            
        return result

# Expose function
def retrieve(query):
    r = Retriever()
    return r.retrieve(query)

import pathlib
import os
import re
import json
import warnings
from typing import List, Dict, Any

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
        self.txt_files = list(self.base_path.glob("*.txt"))
        
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
        except Exception as e:
            # print(f"Warning: CrossEncoder failed to load: {e}")
            self.cross_encoder = None

    def _detect_intent(self, query: str) -> str:
        query_lower = query.lower()
        
        # Listing keywords
        listing_keywords = ["list all", "list the", "list topics", "list summaries", "give me a list", "show all"]
        for k in listing_keywords:
            if k in query_lower:
                return "listing"

        # Structured Pattern Detection
        # Matches: "Chapter 7", "Example 7.2", "Exercise 3.1", "Problem 1.5", "1.2"
        structured_patterns = [
            r"chapter\s*\d+", 
            r"example\s*\d+", 
            r"problem\s*\d+", 
            r"exercise\s*\d+",
            r"question\s*\d+",
            r"\b\d+\.\d+\b"
        ]
        
        for p in structured_patterns:
            if re.search(p, query_lower):
                return "structured"

        return "explanation"

    def _find_file_for_query(self, query: str) -> str:
        """Heuristic to pick the right text file based on query terms."""
        q = query.lower()
        if "example" in q:
            return "examples.txt"
        elif "problem" in q:
            return "problems.txt"
        elif "exercise" in q or "question" in q:
            # Check for both, prioritize exercises.txt
            if (self.base_path / "exercises.txt").exists():
                return "exercises.txt"
            return "exercise.txt" # Common variation
        elif "topic" in q or "chapter" in q:
            return "topics.txt"
        return ""

    def _extract_from_text(self, filename: str, query: str, intent: str) -> str:
        file_path = self.base_path / filename
        if not file_path.exists():
            return f"File {filename} not found."
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Identify Target Chapter/ID
        # Try to find "X.Y" or just "X"
        id_match = re.search(r"(\d+(\.\d+)*)", query)
        target_id = id_match.group(1) if id_match else None
        
        if not target_id:
            return "Could not identify a specific ID (e.g., 7.1) in your query."

        # 2. Logic for Topics (Line-based)
        if filename == "topics.txt":
            # If target_id is just a chapter number (e.g. '7' or '07'), list all 7.x
            # If target_id is specific '7.2', show that line
            lines = content.splitlines()
            matches = []
            for line in lines:
                if line.strip().startswith(target_id):
                    matches.append(line.strip())
            
            if matches:
                return "\n".join(matches)
            else:
                return f"No topics found for ID {target_id}"

        # 3. Logic for Examples/Exercises/Problems (Block-based)
        # We assume blocks start with "Example X.Y", "Question X.Y", "Problem X.Y"
        # We'll try to find the specific block for target_id
        
        # Regex to find the header
        # Covers: Example 1.1, Question 1.1, Exercise 1.1, Problem 1.1
        header_pattern = re.compile(
            r"(Example|Question|Exercise|Problem)\s+" + re.escape(target_id) + r"\s*(.*?)(?=(Example|Question|Exercise|Problem)\s+\d+\.\d+|\Z)", 
            re.IGNORECASE | re.DOTALL
        )
        
        match = header_pattern.search(content)
        if match:
            return match.group(0).strip()
            
        # If strict match failed, maybe the user asked for "Chapter 7" examples in listing mode
        if intent == "listing" and len(target_id.split('.')) == 1:
            # List all items for this chapter
            # Find all headers starting with "{target_id}."
            list_pattern = re.compile(r"((Example|Question|Exercise|Problem)\s+" + re.escape(target_id) + r"\.\d+.*)", re.IGNORECASE)
            headers = [m.group(1) for m in list_pattern.finditer(content)]
            if headers:
                return "**Items found:**\n" + "\n".join([f"- {h}" for h in headers[:50]]) # Limit to 50
            return f"No items found for Chapter {target_id}"

        return f"Exact match for {target_id} not found in {filename}."

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
            # Try to identify which text file to look into
            target_file = self._find_file_for_query(query)
            
            if target_file:
                result["answer"] = self._extract_from_text(target_file, query, intent)
                # Fallback to vector search if text search fails? 
                # The user said "simply use the txt files", implying strictly text search for listing tasks.
                if "not found" in result["answer"] and intent == "structured":
                     # Maybe try semantic search as fallback if specific ID wasn't found?
                     # No, user wants strict adherence to txt listing.
                     pass
            else:
                 # If we can't map query to a file (e.g. "List everything"), maybe list topics?
                 if intent == "listing":
                     result["answer"] = self._extract_from_text("topics.txt", query, intent)
                 else:
                     result["answer"] = "Could not determine which resource (Examples, Exercises, Topics) you are looking for. Please specify."
                
        else: # explanation
            result["answer"] = self._retrieve_and_rank(query)
            
        return result

# Expose function
def retrieve(query):
    r = Retriever()
    return r.retrieve(query)

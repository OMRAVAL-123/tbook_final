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
            self.cross_encoder = None

    def _detect_intent(self, query: str) -> str:
        query_lower = query.lower()
        
        # Listing keywords
        listing_keywords = ["list all", "list the", "list topics", "list summaries", "give me a list", "show all", "list chapter"]
        for k in listing_keywords:
            if k in query_lower:
                return "listing"

        # Structured Pattern Detection
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
        q = query.lower()
        if "summary" in q or "summaries" in q:
            return "summaries.txt"
        elif "example" in q:
            return "examples.txt"
        elif "problem" in q:
            # Check for problems.txt first, then examples.txt (some systems use eg.txt -> examples.txt)
            if (self.base_path / "problems.txt").exists():
                return "problems.txt"
            return "examples.txt"
        elif "exercise" in q or "question" in q:
            if (self.base_path / "exercises.txt").exists():
                return "exercises.txt"
            return "exercise.txt"
        elif "intext" in q or "in-text" in q:
            if (self.base_path / "intext.txt").exists():
                return "intext.txt"
        elif "topic" in q:
            return "topics.txt"
        elif "chapter" in q:
            # If they just say "Chapter 5", maybe they want summary?
            if (self.base_path / "summaries.txt").exists():
                return "summaries.txt"
            return "topics.txt"
            
        # Fallbacks for chemistry
        if "12" in str(self.base_path):
             if (self.base_path / "intext.txt").exists() and re.search(r"\b\d+\.\d+\b", q):
                 return "intext.txt"
                 
        return "examples.txt" # Default

    def _extract_from_text(self, filename: str, query: str, intent: str) -> str:
        file_path = self.base_path / filename
        if not file_path.exists():
            return f"File {filename} not found."
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to find target ID like "7.2" or "1"
        id_match = re.search(r"(\d+(\.\d+)*)", query)
        target_id = id_match.group(1) if id_match else None
        
        if not target_id:
            return "Could not identify a specific ID (e.g., 7.1) in your query."

        # Logic for Topics
        if filename == "topics.txt":
            lines = content.splitlines()
            matches = []
            for line in lines:
                if line.strip().startswith(target_id):
                    matches.append(line.strip())
            if matches: return "\n".join(matches)
            return f"No topics found for ID {target_id}"

        # Listing Logic
        if intent == "listing":
            # If target_id is just a chapter number (no dot)
            if "." not in target_id:
                # Find all headers starting with this chapter
                # Pattern matches "Chapter X", "Example X.Y", "1.1", etc.
                pattern = re.compile(r"^(.*?" + re.escape(target_id) + r"\.\d+.*)$", re.MULTILINE | re.IGNORECASE)
                headers = [m.group(1).strip() for m in pattern.finditer(content)]
                if headers:
                    return f"**Items in Chapter {target_id}**:\n" + "\n".join([f"- {h}" for h in headers[:50]])
            return "No list found for this chapter."

        # Structured Retrieval
        # We need to be very flexible. 
        # Case 1: "Example 7.2"
        # Case 2: "7.2" at start of line
        # Case 3: "Chapter 7 - Example 2" (Maps 7.2 to Chapter 7 Example 2)
        
        patterns = []
        escaped_id = re.escape(target_id)
        
        # Pattern 1: Standard "Example 1.2"
        patterns.append(re.compile(r"(Example|Question|Exercise|Problem|Chapter|Section)\s+" + escaped_id + r"\b", re.I))
        
        # Pattern 2: "1.2" at start of line
        patterns.append(re.compile(r"^\s*" + escaped_id + r"\b", re.M))
        
        # Pattern 3: "Chapter X - Example Y" for "X.Y"
        if "." in target_id:
            ch, eg = target_id.split(".", 1)
            patterns.append(re.compile(r"Chapter\s+" + re.escape(ch) + r"\s*-\s*Example\s+" + re.escape(eg) + r"\b", re.I))
            patterns.append(re.compile(r"Chapter\s+" + re.escape(ch) + r".*?Example\s+" + re.escape(eg) + r"\b", re.I | re.DOTALL))

        found_match = None
        for p in patterns:
            match = p.search(content)
            if match:
                # Found the start. Now find the end.
                # End is the next "Example/Chapter/etc." or "-------" or end of file
                start_idx = match.start()
                # Look ahead for next separator or header
                end_pattern = re.compile(r"\n(Example|Question|Exercise|Problem|Chapter|Section)\s+\d+|\n-{10,}|\Z", re.I)
                end_match = end_pattern.search(content, start_idx + 1)
                end_idx = end_match.start() if end_match else len(content)
                found_match = content[start_idx:end_idx].strip()
                break
        
        if found_match:
            return found_match

        return f"Exact match for {target_id} not found in {filename}."

    def _retrieve_and_rank(self, query: str) -> str:
        if not self.vectorstore:
            return "Error: Vectorstore not initialized."
        try:
            docs = self.retriever_engine.invoke(query)
            doc_texts = [d.page_content for d in docs]
            if not doc_texts: return "No relevant context found."
            if self.cross_encoder:
                pairs = [[query, doc] for doc in doc_texts]
                scores = self.cross_encoder.predict(pairs)
                scored_docs = sorted(zip(doc_texts, scores), key=lambda x: x[1], reverse=True)
                top_docs = [d[0] for d in scored_docs[:5]] 
            else:
                top_docs = doc_texts[:5]
            context = "\n\n".join(top_docs)
            prompt = f"""You are a strict educational assistant.
Use ONLY the provided Context to answer the Question.

Context:
{context}

Question: {query}

Rules:
1. If the provided Context does NOT contain information related to the Question, reply ONLY with: "Sorry, the provided documents do not contain information related to this question. It is out of context."
2. Do NOT use your own general knowledge to answer if the context is missing info.
3. Use LaTeX for math: inline $...$, display $$...$$.
4. If the user mentions people or topics completely unrelated to mathematics/science (like politicians, celebrities, etc.), reject it as "out of context".
"""
            response = self.llm_smart.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error: {e}"

    def retrieve(self, query: str) -> Dict[str, Any]:
        intent = self._detect_intent(query)
        target_file = self._find_file_for_query(query)
        
        result = {"kb": self.base_path.name, "intent": intent, "answer": ""}
        
        if intent in ["structured", "listing"]:
            result["answer"] = self._extract_from_text(target_file, query, intent)
            if "not found" in result["answer"] and target_file == "examples.txt":
                 # Try intext.txt or exercises.txt if it was a structured request
                 for alt in ["intext.txt", "exercises.txt", "problems.txt"]:
                     if (self.base_path / alt).exists():
                         alt_res = self._extract_from_text(alt, query, intent)
                         if "not found" not in alt_res:
                             result["answer"] = alt_res
                             break
        else:
            result["answer"] = self._retrieve_and_rank(query)
        return result

def retrieve(query):
    return Retriever().retrieve(query)

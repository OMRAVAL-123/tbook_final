---
title: Tbook Final
emoji: 🌖
colorFrom: gray
colorTo: pink
sdk: docker
pinned: false
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# 📚 Intelligent Multi-KB Retrieval System

This repository hosts a sophisticated RAG (Retrieval-Augmented Generation) system designed to interact with multiple rigorous academic Knowledge Bases (KBs). The system employs a **router-retriever-merger architecture** with **intent-aware processing** to deliver high-precision answers for both conceptual questions and structured data requests.

## 🚀 Architecture Overview

The processing pipeline consists of three main stages:

### 1. 🧠 Intelligent Routing (`app.py`)
- **Model**: `llama-3.3-70b-versatile` (via Groq)
- **Function**: analyzes the user query and selects the most relevant Knowledge Bases (e.g., `m_11_kb`, `p_12_kb`) based on their summary metadata.
- **Outcome**: Reduces noise by only querying relevant domains.

### 2. 🔍 Intent-Aware Retrieval (Per KB)
Each Knowledge Base operates as an independent unit with its own retrieval logic (`retriever.py`), databases, and vector indices.

The system detects the **User Intent** and branches the logic accordingly:

#### A. Structured & Listing Queries (Strict Mode)
*Triggered by: "Chapter 7 Example 2", "List all topics", "Example 3.1"*
- **Mechanism**: **Text-to-SQL**. The system generates strict SQL queries to fetch data from curated SQLite databases (`examples.db`, `topics.db`).
- **Rule**: **No Semantic Search**. We completely bypass vector search to prevent hallucination of numbers or IDs.
- **Output**: Exact structured data (JSON/Tables) or "Exact match not found".

#### B. Conceptual & Explanation Queries (Semantic Mode)
*Triggered by: "Explain thermodynamics", "Derive the formula for..."*
- **Step 1: Semantic Search (FAISS)**
    - **Model**: `thenlper/gte-small`
    -Retrieves the **Top 10** most relevant chunks from the vector index.
- **Step 2: Cross-Encoder Re-ranking**
    - **Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
    - Re-ranks the top 10 chunks to select the **Top 5** highest quality matches.
- **Step 3: Context-Aware Generation**
    - **Model**: `llama-3.3-70b-versatile`
    - Generates a detailed explanation.
    - **Logic**: Intelligent handling of partial information. If the context is completely irrelevant, it explicitly replies: *"Sorry, out of context"*.

### 3. 🔗 Smart Merging (`app.py`)
The central application aggregates responses from all active KBs:
- **For Structured/Listing Data**: Concatenates results purely without summarization to preserve data integrity.
- **For Explanations**: Synthesizes a single, coherent response, removing redundancies and ensuring LaTeX formatting is preserved.

---

## 📂 File Structure & Data Flow

```
/
├── app.py                  # Main Application (Router & Merger)
├── requirements.txt        # Dependencies
│
├── [kb_folder]/            # Independent Knowledge Bases (e.g., m_11_kb, p_12_kb)
│   ├── retriever.py        # Local retrieval logic (SQL + FAISS + CrossEncoder)
│   ├── index.faiss         # Vector Index (Text Embeddings)
│   ├── *.db                # SQLite Databases (Structured Data: Examples, Topics)
│   ├── summaries.db        # Metadata for Router
│   └── information.txt     # Raw source text
```

## 🛠️ Technology Stack

- **LLM Provider**: Groq (Llama 3.3 70B & Llama 3.1 8B)
- **Embeddings**: `thenlper/gte-small`
- **Reranking**: `sentence-transformers` (Cross-Encoder)
- **Vector Database**: FAISS (CPU)
- **Structured Database**: SQLite
- **Interface**: Streamlit

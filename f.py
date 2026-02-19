import os
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

folders = {
    "m_11_kb": "information.txt",
    "m_12_kb": "data.txt",
    "p_11_kb": "information.txt",
    "p_12_kb": "data.txt",
    "c_11_kb": "information.txt",
    "c_12_kb": "information.txt",
}


embedding = HuggingFaceEmbeddings(
    model_name="thenlper/gte-small",
    model_kwargs={"device": "cuda"},
    encode_kwargs={"batch_size": 32}
)


splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

for folder in tqdm(folders.keys(), desc="Processing KBs"):
    file_name = folders[folder]
    path = os.path.join(folder, file_name)

    if not os.path.exists(path):
        tqdm.write(f"[SKIPPED] {folder} - file not found")
        continue

    tqdm.write(f"[READING] {folder}/{file_name}")

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    tqdm.write(f"[SPLITTING] {folder}")

    chunks = splitter.split_text(text)

    tqdm.write(f"[EMBEDDING] {folder} | Chunks: {len(chunks)}")

    vectorstore = FAISS.from_texts(
        texts=chunks,
        embedding=embedding
    )

    vectorstore.save_local(folder)

    tqdm.write(f"[SAVED] {folder}/index.faiss")

print("\nAll FAISS indexes created successfully.")

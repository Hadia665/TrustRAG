# vector_store.py
import chromadb

COLLECTION = "trustrag_documents"

def _client():
    return chromadb.PersistentClient(path="./chroma_db")

def reset_vector_store():
    try:
        _client().delete_collection(COLLECTION)
    except Exception:
        pass

def create_vector_store(chunks, embeddings, source_name):
    collection = _client().get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}   # MiniLM ke liye better
    )

    ids = [f"{source_name}_{i}" for i in range(len(chunks))]
    docs = [c["text"] for c in chunks]
    embs = embeddings.tolist()
    metas = [{"page": c["page"], "source": source_name} for c in chunks]

    # Batching: bari PDFs mein Chroma ki batch limit hit ho sakti hai
    B = 500
    for i in range(0, len(ids), B):
        collection.upsert(
            ids=ids[i:i+B],
            documents=docs[i:i+B],
            embeddings=embs[i:i+B],
            metadatas=metas[i:i+B],
        )
    return collection
def delete_source(source_name):
    try:
        collection = _client().get_collection(name=COLLECTION)
        collection.delete(where={"source": source_name})
    except Exception:
        pass
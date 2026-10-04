import chromadb
from sentence_transformers import SentenceTransformer


embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


def retrieve_evidence(question, top_k=5):

    client = chromadb.PersistentClient(
        path="./chroma_db"
    )

    collection = client.get_collection(
        name="trustrag_documents"
    )

    question_embedding = embedding_model.encode(
        [question]
    )

    results = collection.query(
        query_embeddings=question_embedding.tolist(),
        n_results=top_k
    )

    evidence = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    for document, metadata in zip(documents, metadatas):

        evidence.append({
            "text": document,
            "page": metadata["page"],
            "file": metadata["source"]
        })

    return evidence
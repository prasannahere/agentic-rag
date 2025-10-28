from embedder import setup_chroma

if __name__ == "__main__":
    collection, embedder = setup_chroma()

    query = "what is encoder and decorder?"
    query_emb = embedder.encode([query]).tolist()
    results = collection.query(query_embeddings=query_emb, n_results=3)

    print("\n🔍 Query Results:")
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
        print(f"#{i} — {meta['file']} [chunk {meta['chunk']}]")
        print(f" {doc}...\n")  # Print first 200 chars

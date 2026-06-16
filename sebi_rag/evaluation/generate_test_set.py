import json
import random
from pathlib import Path

from loguru import logger

from api.config import settings
from api.llm import generate_answer, get_client


def generate_test_queries():
    chunks_dir = Path(settings.processed_data_dir) / "chunks"
    if not chunks_dir.exists():
        logger.error("Chunks directory not found. Run ingestion first.")
        return

    chunk_files = list(chunks_dir.glob("*.json"))
    if len(chunk_files) < 50:
        logger.warning(f"Only {len(chunk_files)} chunks available, sampling all")
        sample_files = chunk_files
    else:
        sample_files = random.sample(chunk_files, 50)

    sampled_chunks = []
    for f in sample_files:
        with open(f) as fh:
            sampled_chunks.append(json.load(fh))

    test_queries = []
    query_types = {
        "sparse": 15,
        "dense": 15,
        "hybrid": 20,
    }

    client = get_client()
    idx = 0

    for query_type, count in query_types.items():
        type_chunks = sampled_chunks[idx : idx + count]
        idx += count

        for i, chunk in enumerate(type_chunks):
            if query_type == "sparse":
                prompt = (
                    f"Given this regulatory text, generate a query that would best be answered by exact keyword matching "
                    f"(e.g., searching for specific circular numbers, section references, or exact phrases).\n\n"
                    f"Text:\n{chunk['text'][:500]}\n\n"
                    f"Generate only the query, nothing else."
                )
            elif query_type == "dense":
                prompt = (
                    f"Given this regulatory text, generate a query that uses different words/synonyms from what appears "
                    f"in the text but asks about the same concept (semantic search would find it, keyword search might not).\n\n"
                    f"Text:\n{chunk['text'][:500]}\n\n"
                    f"Generate only the query, nothing else."
                )
            else:
                prompt = (
                    f"Given this regulatory text, generate a query that requires both finding a specific document/circular "
                    f"AND understanding the semantic meaning of a regulatory concept.\n\n"
                    f"Text:\n{chunk['text'][:500]}\n\n"
                    f"Generate only the query, nothing else."
                )

            try:
                response = client.chat.completions.create(
                    model=settings.llm_model,
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}],
                )
                generated_query = response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Failed to generate query: {e}")
                generated_query = f"What does {chunk.get('circular_number') or chunk.get('title', 'this document')} say?"

            test_queries.append({
                "query_id": f"q{len(test_queries) + 1:03d}",
                "query": generated_query,
                "query_type": query_type,
                "relevant_chunk_ids": [chunk["chunk_id"]],
                "relevant_circular_numbers": [chunk.get("circular_number")] if chunk.get("circular_number") else [],
                "notes": f"Generated from chunk {chunk['chunk_id'][:12]}...",
            })

    output_path = Path("data/evaluation/test_queries.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(test_queries, f, indent=2)

    logger.info(f"Generated {len(test_queries)} test queries to {output_path}")


if __name__ == "__main__":
    generate_test_queries()

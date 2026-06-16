import cohere
from loguru import logger

from api.config import settings


class CohereReranker:
    def __init__(self):
        self._client = cohere.Client(api_key=settings.cohere_api_key)

    def rerank(self, query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
        try:
            texts = [c["text"] for c in chunks]
            response = self._client.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=texts,
                top_n=top_k,
            )
            results = []
            for r in response.results:
                chunk = {**chunks[r.index]}
                chunk["rerank_score"] = r.relevance_score
                results.append(chunk)
            return results
        except Exception as e:
            logger.warning(f"Cohere rerank failed, falling back to local: {e}")
            global _reranker
            _reranker = LocalReranker()
            return _reranker.rerank(query, chunks, top_k)


class LocalReranker:
    def __init__(self):
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        logger.info("Loaded local cross-encoder for reranking")

    def rerank(self, query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
        pairs = [[query, c["text"]] for c in chunks]
        scores = self._model.predict(pairs)

        scored_chunks = []
        for i, chunk in enumerate(chunks):
            c = {**chunk}
            c["rerank_score"] = float(scores[i])
            scored_chunks.append(c)

        scored_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_chunks[:top_k]


_reranker = None


def get_reranker() -> CohereReranker | LocalReranker:
    global _reranker
    if _reranker is None:
        if settings.cohere_api_key and not settings.cohere_api_key.startswith("your_"):
            logger.info("Using Cohere reranker")
            _reranker = CohereReranker()
        else:
            logger.info("COHERE_API_KEY not set, falling back to local cross-encoder")
            _reranker = LocalReranker()
    return _reranker

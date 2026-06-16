import argparse

from loguru import logger

from indexing.es_index import index_all_chunks as es_index_all
from indexing.qdrant_index import index_all_chunks as qdrant_index_all


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="all", choices=["all", "es", "qdrant"])
    args = parser.parse_args()

    if args.source in ("all", "es"):
        logger.info("Indexing chunks to Elasticsearch...")
        es_index_all()

    if args.source in ("all", "qdrant"):
        logger.info("Indexing chunks to Qdrant...")
        qdrant_index_all()

    logger.info("Indexing complete")


if __name__ == "__main__":
    main()

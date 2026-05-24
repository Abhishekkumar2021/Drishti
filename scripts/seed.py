"""Seed Qdrant with the canonical Drishti collection schema."""

from __future__ import annotations

import logging
import sys

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from drishti.config import get_settings

logger = logging.getLogger(__name__)


def main() -> None:
    """Create the Qdrant collection if it does not already exist."""
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()

    logger.info("Seeding Qdrant at %s", settings.qdrant_url)

    try:
        client = QdrantClient(url=settings.qdrant_url)
        collections = client.get_collections().collections
        exists = any(
            collection.name == settings.qdrant_collection_name for collection in collections
        )

        if exists:
            logger.info("Collection '%s' already exists", settings.qdrant_collection_name)
            return

        logger.info("Creating collection '%s'", settings.qdrant_collection_name)
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=settings.openai_embedding_dimensions,
                    distance=Distance.COSINE,
                ),
            },
        )
        logger.info("Collection '%s' created", settings.qdrant_collection_name)
    except Exception:
        logger.exception("Failed to seed Qdrant")
        sys.exit(1)


if __name__ == "__main__":
    main()

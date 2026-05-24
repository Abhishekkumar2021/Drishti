import os
import sys
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("drishti.seed")

def main():
    logger.info("🌱 Seeding database with sample files...")
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection_name = "drishti_chunks"
    
    try:
        client = QdrantClient(url=qdrant_url)
        logger.info(f"Connected to Qdrant at {qdrant_url}")
        
        # Check if collection exists, create if not
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        
        if not exists:
            logger.info(f"Creating collection '{collection_name}'...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": VectorParams(size=1536, distance=Distance.COSINE)
                }
            )
            logger.info(f"Collection '{collection_name}' created.")
        else:
            logger.info(f"Collection '{collection_name}' already exists.")
            
        logger.info("✅ Database seeded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect or seed database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

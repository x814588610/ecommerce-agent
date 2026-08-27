"""建立商品语义检索索引。"""

from sqlmodel import Session

from ecom_agent.commerce.database import create_db_and_tables, engine
from ecom_agent.commerce.seed import seed_products
from ecom_agent.retrieval.factory import (
    get_embedding_provider,
    get_product_vector_store,
    )
from ecom_agent.retrieval.indexer import index_products


def rebuild_product_index() -> int:
    """读取本地商品并重新写入 Qdrant 商品索引。"""

    create_db_and_tables()

    with Session(engine) as session:
        seed_products(session)
        vector_store = get_product_vector_store()

        try:
            return index_products(session, vector_store)
        finally:
            vector_store.client.close()
            get_product_vector_store.cache_clear()
            get_embedding_provider.cache_clear()



if __name__ == "__main__":
    indexed_count = rebuild_product_index()
    print(f"已索引商品数量：{indexed_count}")
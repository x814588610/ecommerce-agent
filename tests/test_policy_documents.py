"""测试售后政策文档。"""

from ecom_agent.retrieval.policy_documents import (
    PolicyDocument,
    get_default_policy_documents,
)


def test_policy_document_builds_text_and_payload() -> None:
    """政策文档应该能生成向量文本和元数据。"""

    document = PolicyDocument(
        policy_id="return-policy",
        title="退货政策",
        content="商品签收后 7 天内可以申请退货。",
    )

    assert "政策标题：退货政策" in document.text
    assert "政策内容：商品签收后 7 天内可以申请退货。" in document.text
    assert document.payload == {
        "policy_id": "return-policy",
        "title": "退货政策",
        "content": "商品签收后 7 天内可以申请退货。",
        "source": "本地售后政策",
    }


def test_default_policy_documents_are_available() -> None:
    """项目应该提供默认售后政策。"""

    documents = get_default_policy_documents()

    assert len(documents) == 4
    assert {document.policy_id for document in documents} == {
        "return-policy",
        "exchange-policy",
        "warranty-policy",
        "refund-policy",
    }


def test_default_policy_documents_have_searchable_content() -> None:
    """默认政策应该包含可用于检索的关键内容。"""

    documents = get_default_policy_documents()
    all_text = "\n".join(document.text for document in documents)

    assert "7 天" in all_text
    assert "换货" in all_text
    assert "保修" in all_text
    assert "退款" in all_text
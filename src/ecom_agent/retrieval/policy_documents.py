"""售后政策文档定义。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PolicyDocument:
    """表示一条可以被检索的售后政策。"""

    policy_id: str
    title: str
    content: str
    source: str = "本地售后政策"

    @property
    def text(self) -> str:
        """生成用于向量化的完整文本。"""

        return "\n".join(
            [
                f"政策标题：{self.title}",
                f"政策内容：{self.content}",
            ]
        )

    @property
    def payload(self) -> dict[str, object]:
        """生成保存到向量数据库的元数据。"""

        return {
            "policy_id": self.policy_id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
        }


def get_default_policy_documents() -> list[PolicyDocument]:
    """返回项目演示使用的默认售后政策。"""

    return [
        PolicyDocument(
            policy_id="return-policy",
            title="退货政策",
            content=(
                "商品签收后 7 天内可以申请退货。商品需要保持完好，"
                "配件、包装和赠品应当齐全。非商品质量问题产生的退货，"
                "退回运费通常由用户承担。"
            ),
        ),
        PolicyDocument(
            policy_id="exchange-policy",
            title="换货政策",
            content=(
                "商品签收后 7 天内发现质量问题，可以申请换货。"
                "换货前需要提供订单信息和商品问题说明，"
                "平台确认后安排寄回检测。"
            ),
        ),
        PolicyDocument(
            policy_id="warranty-policy",
            title="保修政策",
            content=(
                "手机和电脑提供 1 年有限保修服务。人为损坏、进液、"
                "未经授权拆修以及正常外观磨损通常不属于免费保修范围。"
            ),
        ),
        PolicyDocument(
            policy_id="refund-policy",
            title="退款政策",
            content=(
                "退货审核通过后发起退款。原路退款通常需要 3 到 7 个工作日"
                "到账，具体到账时间取决于支付渠道。"
            ),
        ),
    ]
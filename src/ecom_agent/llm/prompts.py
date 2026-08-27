"""电商 Agent 的 Prompt 模板。"""


from langchain_core.prompts import ChatPromptTemplate

CUSTOMER_SERVICE_SYSTEM_PROMPT = """
你是一个电商智能客服助手。

你的职责：
1. 回答用户的商品咨询。
2. 根据用户的价格、品牌、类别和用途要求推荐商品。
3. 查询商品详情和库存。
4. 使用商品工具获取真实数据。

必须遵守：
1. 涉及商品、价格或库存时，必须优先调用工具。
2. 不得编造数据库中不存在的商品。
3. 不得编造价格、库存、品牌或商品参数。
4. 缺货商品不能作为正常推荐结果。
5. 如果没有找到符合条件的商品，要诚实说明。
6. 回答要简洁、清楚，并说明商品名称、价格和库存状态。
7. 退款、取消订单和修改订单属于高风险操作，不能自行执行，必须请求人工审批。
"""


def create_customer_service_prompt() -> ChatPromptTemplate:
    """创建电商 Agent 使用的 Prompt 模板。"""

    return ChatPromptTemplate.from_messages(
        [
            ("system", CUSTOMER_SERVICE_SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )

# E-commerce Agent

基于 FastAPI、LangGraph 和 LangChain 构建的电商智能客服与商品推荐 Agent。

项目支持商品查询、库存查询、商品推荐、多轮对话，以及高风险操作人工审批。

## 功能

- 商品名称、类别、品牌和价格筛选
- 商品推荐
- 商品详情查询
- 库存查询
- 多轮会话记忆
- 退款等高风险请求拦截
- 人工审批批准或拒绝
- FastAPI API 服务
- Streamlit 演示页面
- SQLite 本地商品数据
- pytest 自动化测试
- Ruff 代码质量检查

## 技术栈

- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings
- SQLModel
- SQLite
- LangChain
- LangGraph
- Streamlit
- pytest
- Ruff

## 项目结构

```text
ecommerce-agent/
├── src/ecom_agent/
│   ├── agent/       # Agent 状态、流程、工具和审批逻辑
│   ├── api/         # FastAPI 路由
│   ├── commerce/    # 商品模型、数据库和仓储
│   ├── llm/         # 大语言模型工厂和 Prompt
│   ├── retrieval/   # 检索模块预留目录
│   └── schemas/     # 请求和响应数据模型
├── tests/           # 自动化测试
├── web/             # Streamlit 演示页面
├── data/            # SQLite 数据库目录
├── start_api.ps1    # FastAPI 启动脚本
├── start_web.ps1    # Streamlit 启动脚本
├── pyproject.toml   # 项目依赖和工具配置
├── .env.example     # 环境变量模板
└── .gitignore       # Git 忽略规则
```

## 环境要求

- Windows、macOS 或 Linux
- Python 3.10 或更高版本
- 一个 OpenAI 兼容接口的 API Key

本项目默认使用 DeepSeek API，也可以通过配置切换到其他兼容 OpenAI SDK 的服务。

## 安装

进入项目目录：

```powershell
cd D:\ecommerce-agent
```

创建虚拟环境：

```powershell
py -3.10 -m venv .venv
```

激活虚拟环境：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

安装项目及开发依赖：

```powershell
python -m pip install -e ".[agent,demo,dev]" --no-build-isolation
```

## 配置 API Key

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

然后打开 `.env`，填写真实的 API Key：

```text
LLM_API_KEY=your-api-key
```

`.env` 只保存在本地，并且已经加入 `.gitignore`，不会被 Git 提交。

不要把真实 API Key 写入 Python 源代码、README 或提交信息。

## 启动项目

### 启动 FastAPI

打开第一个 PowerShell 窗口：

```powershell
.\start_api.ps1
```

后端地址：

```text
http://127.0.0.1:8000
```

交互式 API 文档：

```text
http://127.0.0.1:8000/docs
```

### 启动 Streamlit

打开第二个 PowerShell 窗口：

```powershell
.\start_web.ps1
```

演示页面：

```text
http://127.0.0.1:8501
```

启动脚本会自动使用项目虚拟环境、指定 `src` 目录并清理当前进程中的异常代理配置。

## 主要 API

```text
GET  /health
GET  /products
GET  /products/{product_id}
POST /chat
GET  /approvals/{approval_id}
POST /approvals/{approval_id}/decision
```

也可以访问 `/docs`，通过网页直接查看和测试接口。

## 测试

运行全部测试：

```powershell
python -m pytest -q
```

运行 Ruff 检查：

```powershell
python -m ruff check .
```

当前项目验证结果：

```text
69 passed
All checks passed!
```

测试不依赖真实模型 API，使用 Fake Model 和本地测试数据库。

## 安全说明

- `.env` 不提交到 Git
- API Key 不写入源代码
- API Key 不写入日志
- 数据库文件不提交到 Git
- 构建目录和日志目录不提交到 Git
- 退款等高风险操作必须经过人工审批
- 模型不能直接修改商品数据库

## Git 提交

查看当前状态：

```powershell
git status
```

查看提交记录：

```powershell
git log --oneline
```

提交修改：

```powershell
git add .
git commit -m "描述本次修改"
```

提交前建议运行测试和 Ruff。

## 后续计划

- 增加 Qdrant 商品语义检索
- 增加售后政策检索
- 增加订单查询
- 增加更完整的 Agent 评估集
- 增加 Docker Compose
- 增加 GitHub Actions
- 接入真实电商平台接口

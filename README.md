# E-commerce Agent

基于 FastAPI、LangGraph 和 LangChain 构建的电商智能客服与商品推荐 Agent。

项目支持商品查询、库存查询、商品推荐、多轮对话，以及高风险操作人工审批。

[![CI](https://github.com/x814588610/ecommerce-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/x814588610/ecommerce-agent/actions/workflows/ci.yml)

## 功能

- 商品语义搜索
- 商品名称、类别、品牌和价格筛选
- 商品推荐
- 商品详情查询
- 库存查询
- 售后政策 RAG 检索
- 多轮会话记忆
- 意图识别与工具权限控制
- 退款等高风险请求人工审批
- 工具异常捕获和降级回答
- 模型、工具、耗时和错误日志
- 固定评估集和自动化回归
- FastAPI API 服务
- Streamlit 演示页面
- SQLite 本地商品数据
- Docker Compose 运行 Qdrant
- GitHub Actions 自动检查
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
- Qdrant
- FastEmbed
- Streamlit
- Docker Compose
- GitHub Actions
- pytest
- Ruff

## 项目结构

```text
ecommerce-agent/
├── .github/workflows/ci.yml
├── src/ecom_agent/
│   ├── agent/       # Agent 状态、意图、流程、工具、审批和日志
│   ├── api/         # FastAPI 路由
│   ├── commerce/    # 商品模型、数据库和仓储
│   ├── llm/         # 大语言模型工厂和 Prompt
│   ├── retrieval/   # 商品和售后政策向量检索
│   ├── schemas/     # 请求和响应数据模型
│   └── logging_config.py
├── tests/           # 自动化测试
├── evals/           # 固定评估集和评估脚本
├── web/             # Streamlit 演示页面
├── data/            # 本地数据库和 Qdrant 数据
├── docker-compose.yml
├── start_api.ps1
├── start_web.ps1
├── pyproject.toml
├── .env.example
└── .gitignore
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

### 启动 Docker Qdrant

启动 Qdrant 容器：

```powershell
docker compose up -d qdrant
```

检查容器状态：

```powershell
docker compose ps
```

检查 Qdrant 健康状态：

```powershell
Invoke-RestMethod http://127.0.0.1:6333/healthz
```

首次启动 Docker Qdrant，或商品数据和售后政策发生变化后，重新建立索引：

```powershell
$env:PYTHONPATH = "D:\ecommerce-agent\src"

python.exe -m ecom_agent.retrieval.rebuild
python.exe -m ecom_agent.retrieval.rebuild_policies
```

默认索引包含 5 个商品和 4 条售后政策。

项目通过 `.env` 中的 `QDRANT_URL=http://localhost:6333` 连接 Docker Qdrant。
如果没有配置 `QDRANT_URL`，则使用本地 `data/qdrant` 目录。

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

测试不依赖真实模型 API，使用 Fake Model、本地数据库和测试数据。

每次向 `main` 分支推送代码或创建 Pull Request 时，GitHub Actions 会自动执行
Ruff 检查和 pytest 测试。可以在 GitHub 仓库的 `Actions` 页面查看执行结果。

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

- 增加订单查询
- 接入 Saleor GraphQL API
- 增加真实退货和退款流程
- 接入 Langfuse 调用追踪
- 增加管理后台
- 增加更完整的多 Agent 协作
- 接入真实电商平台接口

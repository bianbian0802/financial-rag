# Financial RAG

## 1. 项目定位

这是一个面向金融场景的 RAG 项目，用来完成公开金融文档的解析、检索与问答。

项目目标不是做一个泛用聊天机器人，而是做一个更接近企业内部知识库助手的 AI 应用：

- 能读取金融制度、产品说明、监管文件、年报等资料
- 能根据用户问题召回相关片段
- 能基于召回内容生成回答
- 能给出引用来源，降低幻觉风险
- 能逐步扩展到 Agent、审计日志、权限控制等企业能力

## 2. 为什么做这个项目

这个项目直接服务于你的转型目标：

- 目标岗位：AI 应用开发工程师 / RAG 工程师 / Agent 开发工程师
- 目标方向：金融场景 AI 落地
- 目标价值：把你的后端能力、银行业务理解、需求分析经验和 AI 应用能力串成一条完整主线

## 3. MVP 范围

第一阶段先只做最小闭环，不追求一步到位。

MVP 需要完成：

1. 上传 PDF / Markdown 文档
2. 提取文本并清洗
3. 按规则切片
4. 生成 embedding
5. 存入向量库
6. 根据问题检索相关片段
7. 基于检索结果生成回答
8. 返回引用来源

## 4. 计划技术栈

- `Python`
- `FastAPI`
- `PostgreSQL`
- `pgvector`
- `Redis`
- `Docker Compose`
- `OpenAI-compatible API`
- `bge` 系列中文 embedding / rerank 模型

## 5. 目录结构

```text
financial-rag/
  README.md
  .gitignore
  docs/
    day3-notes.md
    day8-notes.md
    day9-notes.md
    day10-notes.md
  app/
    api/
      v1/
        .gitkeep
    core/
      .gitkeep
    db/
      models/
        .gitkeep
    services/
      .gitkeep
    schemas/
      .gitkeep
    utils/
      .gitkeep
  frontend/
    src/
  tests/
    .gitkeep
  scripts/
    .gitkeep
```

## 6. Day3 完成内容

今天完成的是项目初始化，不是功能开发。

已完成：

1. 创建独立项目目录 `financial-rag`
2. 写出项目定位和 MVP 范围
3. 定义第一版目录结构
4. 预留 `docs`、`app`、`tests`、`scripts` 目录
5. 建立后续学习和开发的落脚点

## 7. Day4 以后怎么接

建议按这个顺序继续：

1. Day4：搭 `FastAPI` 最小服务
2. Day5：补日志、异常处理、配置管理
3. Day6：接入模型 API，完成 `/chat` 接口
4. Day7：补流式返回
5. Day8：接入 Vue 前端聊天页
6. Day9：做文档上传入口
7. Day10 以后：做文档解析、切片、检索

## 8. 当前阶段的验收标准

当前 Day3 的验收标准是：

- 有独立项目目录
- 有清晰 README
- 有基础目录结构
- 后续开发路径明确

这些内容已经具备，可以直接进入 Day4。

## 9. Day4 新增内容

Day4 已经补上了 FastAPI 最小服务骨架，当前新增内容包括：

1. `requirements.txt`：记录基础依赖
2. `app/main.py`：应用入口
3. `app/api/v1/router.py`：v1 路由聚合
4. `app/api/v1/health.py`：健康检查接口
5. `app/core/config.py`：配置管理
6. `app/schemas/health.py`：响应模型
7. `docs/day4-notes.md`：Day4 说明文档

当前最小接口为：

- `GET /api/v1/health`

返回示例：

```json
{
  "status": "ok",
  "service": "financial-rag"
}
```

## 10. Day4 启动命令

等本机安装可用 Python 后，执行：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

启动后可访问：

- `http://127.0.0.1:8000/api/v1/health`
- `http://127.0.0.1:8000/docs`

## 11. Day5 新增内容

Day5 在 Day4 的基础上补了三块工程能力：

1. 日志配置
2. 统一异常处理
3. 更完整的基础配置

新增文件：

1. `app/core/logging.py`
2. `app/core/exceptions.py`
3. `app/core/handlers.py`
4. `app/schemas/error.py`
5. `docs/day5-notes.md`
6. `.env.example`

主要变化：

1. 应用启动时会初始化日志配置
2. 已注册统一异常处理器
3. 已补充 `app_host`、`app_port`、`log_level` 配置
4. 健康检查接口已开始写入日志

## 12. Day5 的价值

Day5 不是增加业务功能，而是让服务更像一个真正可维护的后端项目。

你后面做 `/chat`、`/documents`、`/ask` 时，会直接受益于这些基础能力：

1. 出错时返回结构更统一
2. 日志更容易定位问题
3. 配置不会到处写死

## 13. Day6 新增内容

Day6 的目标是完成第一次真实模型调用闭环。

新增文件：

1. `app/schemas/chat.py`
2. `app/services/chat_service.py`
3. `app/api/v1/chat.py`

更新内容：

1. `requirements.txt` 新增 `httpx`
2. `app/core/config.py` 新增模型调用配置
3. `app/api/v1/router.py` 注册 `/chat` 路由
4. `.env.example` 新增模型环境变量模板
5. `docs/day6-notes.md` 记录 Day6 说明

当前新增接口：

- `POST /api/v1/chat`

请求示例：

```json
{
  "message": "请介绍一下RAG是什么"
}
```

## 14. Day6 运行前准备

在本地实际调模型前，你需要先在 `.env` 中填写：

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=your_openai_compatible_base_url
LLM_CHAT_MODEL=your_model_name
```

如果不配置 `LLM_API_KEY`，接口会返回统一错误响应。

## 15. Day7 新增内容

Day7 的目标是让聊天接口支持流式返回。

本次新增能力：

1. `POST /api/v1/chat` 支持 `stream=true`
2. 流式响应类型为 `text/event-stream`
3. 保持原有普通 JSON 返回不变
4. 增加本地最小测试覆盖普通与流式模式

流式请求示例：

```json
{
  "message": "请用一句话解释 RAG",
  "stream": true
}
```

本地使用 Ollama 时，可以参考：

```env
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=ollama
LLM_CHAT_MODEL=qwen2.5:3b
LLM_TIMEOUT_SECONDS=60
```

更详细的 Day7 说明见 `docs/day7-notes.md`。

## 16. Day8 新增内容

Day8 的目标是把聊天能力接到独立前端工程中。

本次新增能力：

1. 新增 `frontend/`，使用 `Vue 3 + Vite + TypeScript`
2. 实现一个居中的扁平化聊天页面
3. 前端接入 `/api/v1/chat`，支持普通返回和流式返回
4. 支持多轮上下文，前端会通过 `history` 传递历史消息
5. 使用 `Vite` 代理本地开发请求

前端启动命令：

```bash
cd frontend
npm install
npm run dev
```

默认访问地址：

```text
http://127.0.0.1:5173
```

更详细的 Day8 说明见 `docs/day8-notes.md`。

## 17. Day9 新增内容

Day9 的目标是让知识文档先进入系统。

本次新增能力：

1. 新增 `POST /api/v1/documents/upload`
2. 支持上传 `pdf / md / txt / doc / docx`
3. 上传时按块写盘，避免一次性读取大文件
4. 默认支持最高 `25MB` 上传，覆盖 `20MB` 级别 Word 文件
5. 超限时自动删除半成品文件

配置示例：

```env
DOCUMENTS_STORAGE_DIR=data/documents
DOCUMENTS_MAX_UPLOAD_SIZE_MB=25
DOCUMENTS_CHUNK_SIZE_BYTES=1048576
```

更详细的 Day9 说明见 `docs/day9-notes.md`。

## 18. Day10 新增内容

Day10 的目标是把“已上传文件”真正推进到“可被后续切片和检索使用的纯文本”。
本次新增能力：
1. 新增 `POST /api/v1/documents/{document_id}/parse`
2. 上传成功后自动保存本地元数据，后续可直接通过 `document_id` 找回文档
3. 支持解析 `txt / md / pdf / docx`
4. 解析结果会落盘到 `data/documents/parsed/*.json`
5. 返回解析预览、字符数、解析器名称等信息，方便继续做 Day11 切片

当前说明：
1. `.doc` 旧版 Word 文件仍允许上传
2. 但 Day10 暂不直接解析 `.doc`
3. 如果遇到 `.doc`，接口会明确提示先转成 `.docx`

解析结果 JSON 中会包含：
1. 文档基础信息
2. 解析后的完整文本 `extracted_text`
3. 预览文本 `preview_text`
4. 后续切片可直接复用的 `parsed_output_path`

更详细的 Day10 说明见 `docs/day10-notes.md`。

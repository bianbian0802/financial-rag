# Day7 流式返回说明

## 今天完成了什么

Day7 的目标是让 `/api/v1/chat` 支持流式返回，为后续 RAG 问答和前端打字机效果打基础。

本次已完成：

1. 在 `ChatRequest` 中新增 `stream` 开关
2. 在 `ChatService` 中新增上游流式调用和 SSE 转发能力
3. 让 `POST /api/v1/chat` 同时支持普通 JSON 和流式 SSE
4. 新增一个居中的聊天演示页，支持对话式流式返回
5. 支持通过 `history` 传递历史消息，让前端多轮对话具备上下文
6. 增加最小测试，覆盖普通模式、流式模式和 payload 组装
7. 验证本地 Ollama 的 OpenAI-compatible 接口可联通

## 为什么 Day7 要做流式返回

普通返回适合后端先验证闭环，但真实 AI 应用通常还需要更好的交互体验：

1. 用户可以更早看到模型开始输出
2. 前端更容易做逐字显示效果
3. 后面接 RAG 时，长回答的等待体感会更好

## 当前接口设计

当前仍然保持一个接口：

- 方法：`POST`
- 路径：`/api/v1/chat`

默认情况下：

- `stream=false` 或不传时，返回 Day6 的 JSON 结构

流式情况下：

- `stream=true` 时，返回 `text/event-stream`
- 数据格式保持 OpenAI-compatible 的 `data: {...}` 和结束标记 `data: [DONE]`

## 请求示例

普通模式：

```json
{
  "message": "请介绍一下 RAG 是什么"
}
```

流式模式：

```json
{
  "message": "请介绍一下 RAG 是什么",
  "stream": true
}
```

带历史消息的对话模式：

```json
{
  "message": "那它在金融知识库里有什么价值？",
  "stream": true,
  "history": [
    {
      "role": "user",
      "content": "请先解释一下什么是 RAG"
    },
    {
      "role": "assistant",
      "content": "RAG 是检索增强生成，会先检索相关资料，再基于资料生成回答。"
    }
  ]
}
```

## 本地 Ollama 配置示例

如果你本机使用 Ollama，并且已经拉取好模型，例如 `qwen2.5:3b`，可以使用下面的 `.env` 配置：

```env
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=ollama
LLM_CHAT_MODEL=qwen2.5:3b
LLM_TIMEOUT_SECONDS=60
```

说明：

1. 当前代码已经兼容本地地址不强制要求真实 API Key
2. 为了和 OpenAI-compatible 习惯保持一致，示例里仍保留 `LLM_API_KEY=ollama`

## 联调命令

启动服务：

```bash
uvicorn app.main:app --reload
```

打开演示页：

```text
http://127.0.0.1:8000/api/v1/chat/playground
```

这个页面会直接请求同源的 `/api/v1/chat`，可以切换普通模式和流式模式，方便你观察 SSE 的实时输出。
现在页面已经是居中的聊天窗口，并且会把页面上的历史消息通过 `history` 一并传给后端。

测试普通模式：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/chat" ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"请用一句话解释 RAG\"}"
```

测试流式模式：

```bash
curl -N -X POST "http://127.0.0.1:8000/api/v1/chat" ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"请用一句话解释 RAG\",\"stream\":true}"
```

## 当前这一步的价值

Day7 做完后，你的项目已经具备：

1. 最小健康检查接口
2. 普通聊天接口
3. 流式聊天接口
4. 最小多轮聊天页面

下一步就可以更自然地进入文档上传、解析、切片和检索链路。

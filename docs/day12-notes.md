# Day12 Embedding 说明

## 什么是 Embedding

Embedding 可以理解成“把文本变成向量坐标”。

一段文本本身是人能直接读懂的字符串，但机器做相似度搜索时，更擅长处理数字向量。

比如：

1. “年报披露营业收入增长”
2. “公司营收同比上涨”

这两句话字面不一样，但语义很接近。
Embedding 的作用，就是把这种“语义接近”的文本映射到更接近的向量空间里。

## 为什么要做 Embedding

在 RAG 里，Embedding 是检索的基础。

如果不做 embedding，系统很难判断：

1. 用户问的是不是和文档里的某一段意思接近
2. 哪个 chunk 和问题最相关
3. 哪些片段应该优先送给大模型

有了 embedding 之后，就可以：

1. 把文档 chunk 变成向量
2. 把用户问题也变成向量
3. 通过向量相似度找出最接近的 chunk

这就是后面“语义检索”的核心。

## Embedding 常见方式

当前项目里最适合的做法，是用 OpenAI-compatible 的 `embeddings` 接口。

常见有两种：

1. 单条请求
   - 一次只发一个文本
   - 实现简单
   - 速度相对慢

2. 批量请求
   - 一次发多个文本
   - 网络开销更小
   - 更适合多个 chunk 的场景

Day12 里我选的是批量请求。

## 本次新增接口

- 方法：`POST`
- 路径：`/api/v1/documents/{document_id}/embed`

## 当前处理流程

1. 读取 Day11 生成的 `chunks/{document_id}.json`
2. 取出每个 chunk 的 `text`
3. 调用 embedding 接口生成向量
4. 把向量写回本地 JSON

## 当前新增配置

```env
EMBEDDING_BASE_URL=http://127.0.0.1:11434/v1
EMBEDDING_API_KEY=ollama
EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBEDDING_BATCH_SIZE=8
EMBEDDING_TIMEOUT_SECONDS=60
```

## 为什么本次选择 OpenAI-compatible 方式

因为你现在前面的聊天接口已经按 OpenAI-compatible 方式统一过了。

这样 Day12 继续沿用同样的请求风格，代码会更统一：

1. `/chat/completions` 做聊天
2. `/embeddings` 做向量

如果以后你切换到别的模型服务，只要它兼容这套接口，后端改动就会比较小。

## 本地 Ollama 的建议

你当前机器上已经有 `qwen2.5:3b`，但它是聊天模型，不是 embedding 模型。

如果你想本地真正跑 Day12，建议额外拉一个 embedding 模型，例如：

```bash
ollama pull qwen3-embedding:0.6b
```

## 结果会保存到哪里

```text
data/documents/embeddings/
```

## 测试方式

先启动后端：

```powershell
cd d:\Users\yuanpp\CursorWork\financial-rag
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

按顺序执行：

1. 上传文档
2. 解析文档
3. 切片文档
4. 生成 embedding

或者直接在 Swagger 里按顺序调这三个接口：

```text
http://127.0.0.1:8000/docs
```

## 这一步的价值

Day12 完成后，你已经从“文本处理”进入到“向量化检索准备”。

下一步 Day13 就可以开始做：

1. 向量检索
2. top-k 召回
3. 把命中的 chunk 组装成回答上下文

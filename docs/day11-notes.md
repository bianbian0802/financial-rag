# Day11 文本清洗与切片说明

## 今天完成了什么

Day11 的目标，是把 Day10 已经解析出的纯文本继续往下处理，产出后续做 embedding 和检索时更好用的 chunk。

本次已经完成：

1. 新增 `POST /api/v1/documents/{document_id}/chunk`
2. 读取 Day10 的解析结果 JSON，而不是重新解析原文件
3. 做轻量文本清洗，统一空白和换行
4. 按固定字符长度切片
5. 支持 chunk overlap，保证上下文衔接更自然
6. 将切片结果保存到本地 JSON

## 为什么 Day11 要单独做“切片”

RAG 里最常见的一步就是“不要把整篇文档直接拿去做向量化”，而是先拆成多个较小片段。

这样做的原因有三个：

1. 整篇文档太长，不适合直接检索
2. 用户问题通常只对应文档中的一小段内容
3. 切片后更容易做召回、引用和命中定位

所以 Day11 的目标不是“回答问题”，而是先把文本准备成更适合检索的数据单元。

## 当前新增接口

- 方法：`POST`
- 路径：`/api/v1/documents/{document_id}/chunk`

## 当前切片流程

当前接口收到 `document_id` 后，会按下面的顺序处理：

1. 找到 Day10 已经保存好的 `parsed/{document_id}.json`
2. 读取里面的 `extracted_text`
3. 做轻量清洗
4. 按设定的字符长度切片
5. 给相邻 chunk 保留一部分重叠内容
6. 把结果写入 `chunks/{document_id}.json`

## 当前文本清洗做了什么

这次只做了轻量处理，没有上复杂规则：

1. 统一换行符
2. 压缩连续空格和制表符
3. 去掉多余空行
4. 保留段落结构，方便后续断点更自然

这一步的目标是“让 chunk 更稳定”，而不是过早做重清洗。

## 当前切片规则

这次采用的是简单稳定的字符切片策略：

1. 每个 chunk 目标长度由 `DOCUMENT_CHUNK_SIZE` 控制
2. 相邻 chunk 的重叠长度由 `DOCUMENT_CHUNK_OVERLAP` 控制
3. 在到达目标长度附近时，优先尝试在这些位置断开：
   - 空段落
   - 换行
   - 句号、问号、感叹号
   - 逗号、空格

这样做的好处是：

1. 实现简单
2. 容易测试
3. 对当前学习项目已经足够

## 当前默认配置

```env
DOCUMENT_CHUNK_SIZE=800
DOCUMENT_CHUNK_OVERLAP=120
DOCUMENT_CHUNK_PREVIEW_LIMIT=180
```

含义：

1. `DOCUMENT_CHUNK_SIZE`
   - 单个 chunk 的目标最大字符数
2. `DOCUMENT_CHUNK_OVERLAP`
   - 相邻 chunk 之间重复保留的字符数
3. `DOCUMENT_CHUNK_PREVIEW_LIMIT`
   - 返回给接口时的 chunk 预览长度

## 切片结果保存位置

Day10 的解析结果在：

```text
data/documents/parsed/
```

Day11 的切片结果在：

```text
data/documents/chunks/
```

## 切片结果示例

```json
{
  "document_id": "abc123",
  "source_parsed_output_path": "data/documents/parsed/abc123.json",
  "chunk_count": 3,
  "chunk_size": 800,
  "chunk_overlap": 120,
  "cleaned_char_count": 1760,
  "chunks_output_path": "data/documents/chunks/abc123.json",
  "status": "chunked",
  "chunked_at": "2026-05-29T17:00:00Z",
  "chunks": [
    {
      "chunk_id": "abc123-chunk-0000",
      "chunk_index": 0,
      "text": "这里是第一段切片文本",
      "char_count": 320,
      "start_char_index": 0,
      "end_char_index": 320,
      "preview_text": "这里是第一段切片文本"
    }
  ]
}
```

## 怎么测试

先启动后端：

```powershell
cd d:\Users\yuanpp\CursorWork\financial-rag
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

先上传：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/documents/upload" `
  -F "file=@D:\Users\yuanpp\Desktop\sample.md"
```

再解析：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/documents/YOUR_DOCUMENT_ID/parse"
```

最后切片：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/documents/YOUR_DOCUMENT_ID/chunk"
```

也可以直接去 Swagger：

```text
http://127.0.0.1:8000/docs
```

## 这一步的价值

Day11 做完后，你现在已经具备：

1. 文档上传
2. 文档解析
3. 文本切片

这意味着你的文档链路已经从“原文件”推进到了“可检索的文本片段”。

下一步 Day12 就可以自然继续做：

1. embedding 生成
2. chunk 向量化存储
3. 检索接口雏形

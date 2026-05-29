# Day10 文档解析说明

## 今天完成了什么

Day10 的目标，是把 Day9 上传进来的文件继续往下推进，真正转成后续 RAG 能使用的纯文本。

本次已经完成：

1. 新增 `POST /api/v1/documents/{document_id}/parse`
2. 上传成功后自动保存文档元数据，后续可以只靠 `document_id` 找回文件
3. 支持解析 `txt / md / pdf / docx`
4. 解析结果会保存到本地 JSON，方便后面 Day11 直接做切片
5. 对 `.doc` 返回清晰限制提示，避免静默失败

## 为什么 Day10 先做“解析”，不急着做“切片”

这是一个很关键的拆分。

如果把“上传、解析、切片、向量化”一次性全塞进一个接口里：

1. 排错会很困难
2. 一旦出问题，不知道卡在上传、解析还是切片
3. 后续测试成本会明显升高

所以当前先把 Day10 单独做成一个小闭环：

1. 上传文件
2. 根据 `document_id` 解析文件
3. 产出统一的纯文本结果

这样后面的 Day11 就只需要专注“怎么切片”。

## 当前新增接口

- 方法：`POST`
- 路径：`/api/v1/documents/{document_id}/parse`

## 当前支持解析的格式

1. `.txt`
2. `.md`
3. `.pdf`
4. `.docx`

## 当前对 `.doc` 的处理

当前仍然允许上传 `.doc`，但暂不直接解析。

原因很实际：

1. `.doc` 是老的二进制 Word 格式
2. Python 里要稳定解析 `.doc`，通常需要更重的依赖或外部程序
3. 这会让当前学习项目的复杂度一下子上升很多

所以当前接口会明确返回提示：建议先转成 `.docx` 再解析。

## 解析结果会保存到哪里

上传后的原文件仍然保存在：

```text
data/documents/
```

上传元数据会保存在：

```text
data/documents/metadata/
```

解析后的结果会保存在：

```text
data/documents/parsed/
```

## 解析结果示例

```json
{
  "document_id": "abc123",
  "original_filename": "report.docx",
  "stored_filename": "abc123.docx",
  "file_extension": ".docx",
  "source_storage_path": "data/documents/abc123.docx",
  "parser_name": "python-docx",
  "status": "parsed",
  "extracted_char_count": 1820,
  "preview_text": "这是解析后的文本预览……",
  "parsed_output_path": "data/documents/parsed/abc123.json",
  "parsed_at": "2026-05-29T11:00:00Z"
}
```

对应的解析文件 JSON 中，还会包含完整文本字段：

```json
{
  "extracted_text": "这里是完整解析文本"
}
```

## 当前用到的解析方式

1. `txt / md`：按文本文件读取
2. `pdf`：使用 `pypdf`
3. `docx`：使用 `python-docx`

## 测试方式

先启动后端：

```powershell
cd d:\Users\yuanpp\CursorWork\financial-rag
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

上传文件：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/documents/upload" `
  -F "file=@D:\Users\yuanpp\Desktop\sample.docx"
```

拿到返回里的 `document_id` 后，再调用解析接口：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/documents/YOUR_DOCUMENT_ID/parse"
```

或者直接去 Swagger 页面测试：

```text
http://127.0.0.1:8000/docs
```

## 这一步的价值

Day10 做完后，你现在已经具备：

1. 聊天接口
2. 流式聊天接口
3. Vue 前端聊天页
4. 文档上传入口
5. 文档解析入口

下一步 Day11 就可以继续做：

1. 文本清洗
2. 文档切片
3. 为向量化做输入准备

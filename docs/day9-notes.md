# Day9 文档上传接口说明

## 今天完成了什么

Day9 的目标是补齐 RAG 的第一个入口：让外部文档先进入系统。

本次已完成：

1. 新增 `POST /api/v1/documents/upload`
2. 支持上传 `pdf / md / txt / doc / docx`
3. 上传时按块写盘，避免把大文件一次性读入内存
4. 默认支持最高 `25MB` 的上传大小，因此可以覆盖你当前 `20MB` 级别的 Word 文件需求
5. 超过大小限制时会删除半成品文件，避免磁盘残留
6. 返回统一的上传元信息，方便后续 Day10 解析流程继续往下接

## 当前接口设计

- 方法：`POST`
- 路径：`/api/v1/documents/upload`
- 请求类型：`multipart/form-data`
- 文件字段名：`file`

## 当前支持格式

1. `.pdf`
2. `.md`
3. `.txt`
4. `.doc`
5. `.docx`

## 返回示例

```json
{
  "document_id": "3c3c8ad618ef4b5a99b851dfcbc79f87",
  "original_filename": "report.docx",
  "stored_filename": "3c3c8ad618ef4b5a99b851dfcbc79f87.docx",
  "file_extension": ".docx",
  "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "size_bytes": 20971520,
  "storage_path": "data/documents/3c3c8ad618ef4b5a99b851dfcbc79f87.docx",
  "status": "uploaded",
  "uploaded_at": "2026-05-29T10:00:00Z"
}
```

## 为什么这里要分块写盘

如果直接 `await file.read()` 一次性读完整文件：

1. 大文件会瞬间占用更多内存
2. 后面多个用户同时上传时更容易顶高内存
3. 不利于后续继续扩展到更大文档

所以当前实现用了“循环读取固定块大小，再写入磁盘”的方式。

## 当前默认配置

`.env` 可配置项：

```env
DOCUMENTS_STORAGE_DIR=data/documents
DOCUMENTS_MAX_UPLOAD_SIZE_MB=25
DOCUMENTS_CHUNK_SIZE_BYTES=1048576
```

含义：

1. 上传文件默认保存到 `data/documents`
2. 默认允许最大 `25MB`
3. 默认按 `1MB` 一块写入磁盘

## 测试示例

PowerShell 上传示例：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/documents/upload" `
  -F "file=@D:\Users\yuanpp\Desktop\sample.docx"
```

## 当前这一步的价值

Day9 做完后，你已经具备：

1. 聊天接口
2. 流式聊天接口
3. Vue 聊天前端
4. 文档上传入口

下一步 Day10 就可以继续做文档解析，把上传后的文件真正转成文本内容。

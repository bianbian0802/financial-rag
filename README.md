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
4. Day7 以后：做文档上传、解析、切片、检索

## 8. 当前阶段的验收标准

当前 Day3 的验收标准是：

- 有独立项目目录
- 有清晰 README
- 有基础目录结构
- 后续开发路径明确

这些内容已经具备，可以直接进入 Day4。

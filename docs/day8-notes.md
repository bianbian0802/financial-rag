# Day8 Vue 前端接入说明

## 今天完成了什么

Day8 的目标是把 Day7 的流式聊天能力真正接到一个可扩展的前端工程里，而不是继续堆单个 HTML 文件。

本次已完成：

1. 新增 `frontend/` 目录，使用 `Vue 3 + Vite + TypeScript`
2. 做了一个居中的扁平化聊天页面
3. 接入 `POST /api/v1/chat`，支持普通返回和流式返回
4. 使用 `fetch + ReadableStream` 解析 SSE 增量内容
5. 保留对话历史，并通过 `history` 一并传给后端
6. 配置 `Vite` 开发代理，默认把 `/api` 转发到 `http://127.0.0.1:8000`

## 为什么这里不继续用单个 HTML

单个 HTML 适合学习和临时联调，但项目一旦进入下面这些需求，就会迅速变得难维护：

1. 多轮对话
2. 流式状态更新
3. 文件上传
4. 引用来源展示
5. 会话列表

所以 Day8 开始，把前端升级为独立工程更合适。

## 当前前端结构

```text
frontend/
  index.html
  package.json
  tsconfig.json
  tsconfig.app.json
  vite.config.ts
  .env.example
  src/
    App.vue
    main.ts
    style.css
    env.d.ts
    lib/
      chat-client.ts
    types/
      chat.ts
```

## 当前页面能力

现在这个前端页面已经具备：

1. 居中的聊天布局
2. 用户 / 助手消息气泡
3. 流式回复实时渲染
4. 系统提示词输入
5. 清空输入 / 清空会话
6. 调试日志区，方便继续学习 SSE

## 启动方式

先启动后端：

```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

再启动前端：

```bash
cd frontend
npm install
npm run dev
```

启动后访问：

```text
http://127.0.0.1:5173
```

## 代理和接口说明

开发环境下，前端不会直接写死后端完整地址，而是通过 `vite.config.ts` 中的代理把：

- `/api/*`

转发到：

- `http://127.0.0.1:8000`

这样做的好处是：

1. 本地开发简单
2. 不需要手动处理浏览器跨域
3. 后续切环境时更清晰

如果你后面需要显式指定后端地址，可以在 `frontend/.env` 中配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 当前这一步的价值

Day8 做完后，你已经从“后端接口练习项目”进入到了“前后端协同的 AI 应用原型”阶段。

下一步可以自然继续：

1. 接文档上传页面
2. 展示引用来源卡片
3. 增加会话列表
4. 接真正的 RAG 检索接口

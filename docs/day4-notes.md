# Day4 FastAPI 最小服务说明

## 今天完成了什么

Day4 的目标是把项目从“只有目录和文档”推进到“具备最小后端服务骨架”。

本次已完成：

1. 新增 `requirements.txt`
2. 新增 FastAPI 应用入口 `app/main.py`
3. 新增 v1 路由聚合文件 `app/api/v1/router.py`
4. 新增健康检查接口 `app/api/v1/health.py`
5. 新增配置文件 `app/core/config.py`
6. 新增响应模型 `app/schemas/health.py`

## 为什么 Day4 先做健康检查接口

先做 `/api/v1/health` 的原因不是它业务复杂，而是它非常适合做后端项目的第一步：

1. 能快速验证服务是否成功启动
2. 能让你熟悉路由、响应模型、配置、入口文件这些核心概念
3. 它足够小，后续排错成本低

## 现在的接口设计

当前服务只有一个接口：

- `GET /api/v1/health`

预期返回：

```json
{
  "status": "ok",
  "service": "financial-rag"
}
```

## FastAPI 在这个项目里扮演什么角色

FastAPI 负责把你的能力组织成“可调用服务”。

后面这些功能，都会以 API 的形式挂在这个项目上：

1. 聊天接口 `/chat`
2. 文档上传接口 `/documents`
3. 检索接口 `/retrieve`
4. 问答接口 `/ask`
5. 评估接口 `/eval`

## 启动
执行：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

启动后访问：

- `http://127.0.0.1:8000/api/v1/health`
- `http://127.0.0.1:8000/docs`

## Day4 的验收标准

Day4 完成的标准是：

1. 项目有可启动的 FastAPI 入口
2. 有基础路由结构
3. 有一个最小可验证接口
4. 有配置文件和响应模型

这些内容现在都已经具备。

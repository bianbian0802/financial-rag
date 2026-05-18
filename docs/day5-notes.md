# Day5 日志、异常处理、配置管理说明

## 今天完成了什么

Day5 的目标是给 Day4 的最小服务骨架补上基础工程能力。

本次已完成：

1. 新增日志配置文件 `app/core/logging.py`
2. 新增自定义异常类型 `app/core/exceptions.py`
3. 新增统一异常处理器 `app/core/handlers.py`
4. 新增统一错误响应模型 `app/schemas/error.py`
5. 扩展配置文件，增加主机、端口和日志级别
6. 更新健康检查接口，让它开始记录日志
7. 新增 `.env.example` 作为本地配置模板

## 为什么要先做这三件事

如果没有这三块能力，后面服务一复杂就会出现这些问题：

1. 出错时返回结构不统一
2. 控制台很难看出具体发生了什么
3. 配置分散在各个文件里，维护成本高

所以 Day5 的本质不是“多写几个文件”，而是提前把后续开发最容易乱掉的地方收拢起来。

## 当前新增的配置项

当前 `app/core/config.py` 已补充：

1. `app_host`
2. `app_port`
3. `log_level`

后面你还可以继续往这里加：

1. `database_url`
2. `redis_url`
3. `openai_api_key`
4. `embedding_model_name`

## 当前错误处理策略

现在应用已经有三层异常处理：

1. `AppException`
   用于业务代码主动抛出可预期错误
2. `RequestValidationError`
   用于处理请求参数校验失败
3. `Exception`
   兜底处理未知错误

这样做的好处是，后面接口即使报错，也能尽量维持统一返回结构。

## 你现在可以怎么验证

启动服务后先访问：

- `http://127.0.0.1:8000/api/v1/health`

如果终端里能看到 health check 的日志，说明 Day5 的日志接入已经生效。

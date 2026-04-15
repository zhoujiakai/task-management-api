# 任务：构建任务管理 API

## 任务描述

开发一个用于任务管理系统的 RESTful API。该 API 应允许用户创建、读取、更新和删除任务，并在任务完成时发送异步通知。使用 Python 3.10+，注重编写简洁、可用于生产环境的代码。

## 时间分配建议

- **20 分钟**：规划与环境搭建（虚拟环境、依赖安装）。
- **60 分钟**：核心功能实现（接口端点、数据库集成）。
- **30 分钟**：异步功能与测试。
- **10 分钟**：文档整理与代码清理。

## 详细需求

### 1. 框架与项目搭建

- 使用 **FastAPI**，因其内置异步支持、自动文档生成（通过 Swagger）以及类型安全特性。
- 安装依赖：`fastapi`、`uvicorn`、`sqlalchemy`、`pydantic`、`pytest`、`asyncio`（内置）。
- **数据库**：使用 SQLite 以简化配置——无需外部数据库服务。使用 SQLAlchemy ORM 定义 `Task` 模型，包含以下字段：
  - `id`（int，主键）
  - `title`（str）
  - `description`（str，可选）
  - `status`（枚举：`'pending'`、`'completed'`）
  - `due_date`（datetime）

### 2. API 接口

- **POST /tasks**：创建新任务。请求体：包含 `title`、`description`、`due_date` 的 JSON。返回创建的任务及其 ID。
- **GET /tasks**：列出所有任务，支持可选查询参数进行过滤（例如 `?status=pending`）。
- **GET /tasks/{id}**：获取单个任务。
- **PUT /tasks/{id}**：更新任务（例如标记为已完成）。当状态变更为 `'completed'` 时，触发异步通知。
- **DELETE /tasks/{id}**：删除任务。
- 实现速率限制或基本身份认证（例如通过 `fastapi.security` 使用 API Key）以防止滥用。

### 3. 异步组件

- 使用 `asyncio` 创建后台任务，在任务完成时发送模拟邮件（例如打印到控制台或记录日志：`"Email sent for task {id}"`）。

### 4. 数据处理与校验

- 使用 **Pydantic** 模型定义请求/响应结构，强制执行类型和校验规则（例如 `due_date` 必须是未来日期）。
- 优雅地处理错误：为未找到的任务和校验失败定义自定义异常（返回 400/404 状态码及错误信息）。

### 5. 测试

- 使用 **pytest** 编写测试，覆盖以下场景：
  - 成功创建和获取任务。
  - 异步通知触发。
  - 错误情况（例如无效日期）。
- 目标达到 **70% 以上覆盖率**，以体现对测试驱动开发（TDD）的理解。

### 6. 优化与最佳实践

- 使用环境变量管理配置（例如通过 `dotenv`）。
- 使用 `logging` 模块实现日志记录。
- 确保异步上下文中数据库访问的线程安全性。
- **加分项**（如有时间）：添加分页功能（例如 `limit`/`offset`）、使用 `functools.lru_cache` 实现缓存，或集成外部 API（例如通过 `requests` 调用 OpenWeather 等免费接口获取 `due_date` 当天的天气信息）。

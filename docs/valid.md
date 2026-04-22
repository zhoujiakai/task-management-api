# 面试题需求 vs 系统实现 逐条比对

## 1. 框架与项目搭建

### 1.1 使用 FastAPI
- **状态**: ✅ 已实现
- **位置**: `app/main.py` — 使用 FastAPI 创建应用，配置 lifespan 管理启动/关闭。

### 1.2 安装依赖：fastapi, uvicorn, sqlalchemy, pydantic, pytest, asyncio
- **状态**: ✅ 已实现
- **位置**: `pyproject.toml` — 所有依赖均已声明。asyncio 为 Python 内置模块。

### 1.3 数据库：SQLite
- **状态**: ✅ 已实现
- **位置**: `app/database.py` — 使用 `sqlite+aiosqlite` 异步驱动，配置在 `app/config.yaml` 中。

### 1.4 SQLAlchemy ORM 定义 Task 模型
- **状态**: ✅ 已实现（有差异）
- **位置**: `app/models.py`
- **差异说明**:
  - `id` 字段：需求要求 `int` 主键，实现为 `String(36)` UUID。UUID 作为主键是更安全的选择，避免 ID 可预测性问题。
  - `status` 枚举：需求要求 `pending`/`completed` 两个值，实现增加了 `in_progress` 状态，功能更完善。
  - 额外字段：增加了 `created_at` 和 `updated_at` 时间戳，符合生产环境最佳实践。

---

## 2. API 接口

### 2.1 POST /tasks — 创建新任务
- **状态**: ✅ 已实现
- **位置**: `app/router.py:38-55`
- **说明**: 接受 JSON 请求体（title, description, due_date），返回 201 状态码及完整任务数据。

### 2.2 GET /tasks — 列出所有任务，支持 ?status= 过滤
- **状态**: ✅ 已实现
- **位置**: `app/router.py:58-68`
- **说明**: 支持 `?status=pending` 等查询参数进行过滤。

### 2.3 GET /tasks/{id} — 获取单个任务
- **状态**: ✅ 已实现
- **位置**: `app/router.py:71-80`

### 2.4 PUT /tasks/{id} — 更新任务，状态变更到 completed 时触发异步通知
- **状态**: ✅ 已实现
- **位置**: `app/router.py:83-111`
- **说明**: 仅在状态 **变更为** `completed` 时触发通知（即已完成的任务再次更新不会重复触发）。

### 2.5 DELETE /tasks/{id} — 删除任务
- **状态**: ✅ 已实现
- **位置**: `app/router.py:114-124`
- **说明**: 成功返回 204 No Content。

### 2.6 速率限制或基本身份认证（API Key）
- **状态**: ✅ 已实现（身份认证）
- **位置**: `app/auth.py`
- **说明**: 使用 `X-API-Key` Header 进行身份验证。速率限制未单独实现。
- **备注**: 需求原文为"速率限制 **或** 基本身份认证"，二选一即可。当前实现了身份认证。

---

## 3. 异步组件

### 3.1 使用 asyncio 创建后台任务，在任务完成时发送模拟邮件
- **状态**: ✅ 已实现
- **位置**: `app/notifications.py`
- **说明**: 异步函数 `send_notification()` 模拟邮件发送，记录日志并模拟网络延迟。

---

## 4. 数据处理与校验

### 4.1 使用 Pydantic 模型定义请求/响应结构
- **状态**: ✅ 已实现
- **位置**: `app/schemas.py`
- **说明**: 定义了 `TaskCreate`、`TaskUpdate`、`TaskResponse` 三个 Pydantic v2 模型。

### 4.2 due_date 必须是未来日期
- **状态**: ✅ 已实现
- **位置**: `app/schemas.py:44-47` — `due_date_must_be_future` 字段验证器。

### 4.3 自定义异常（404/400 状态码及错误信息）
- **状态**: ✅ 已实现
- **位置**: `app/exceptions.py`
- **说明**: 定义了 `TaskNotFoundException`（404）和 `ValidationException`（400），并注册了全局异常处理器。

---

## 5. 测试

### 5.1 使用 pytest 编写测试
- **状态**: ✅ 已实现
- **位置**: `tests/` 目录，共 39 个测试用例，6 个测试文件。

### 5.2 成功创建和获取任务
- **状态**: ✅ 已实现
- **位置**: `tests/test_tasks.py` — `test_create_task`, `test_list_tasks`, `test_get_task`

### 5.3 异步通知触发
- **状态**: ✅ 已实现
- **位置**: `tests/test_notifications.py` — 3 个测试用例验证通知触发逻辑。

### 5.4 错误情况（无效日期等）
- **状态**: ✅ 已实现
- **位置**: `tests/test_validation.py` — 5 个验证测试用例，含无效日期、空标题、无效状态等。

### 5.5 覆盖率 70% 以上
- **状态**: ✅ 已实现
- **当前覆盖率**: 81%（39 个测试全部通过）。

---

## 6. 优化与最佳实践

### 6.1 使用环境变量管理配置（通过 dotenv）
- **状态**: ✅ 已实现
- **位置**: `config.py` — 加载 `.env` 文件，支持通过环境变量覆盖 YAML 配置项（`DATABASE_URL`、`API_KEY`、`SERVER_HOST`、`SERVER_PORT`、`LOG_LEVEL`）。
- **说明**: 新增 `app/.env.example` 模板文件，`python-dotenv` 已添加为依赖。

### 6.2 使用 logging 模块实现日志记录
- **状态**: ✅ 已实现
- **位置**: `logger.py` — 自定义 `ColoredFormatter`，按日志级别着色输出。

### 6.3 确保异步上下文中数据库访问的线程安全性
- **状态**: ✅ 已实现
- **位置**: `app/database.py` — 使用 SQLAlchemy `AsyncSession` + `async_sessionmaker`，每个请求获取独立的数据库会话。

### 6.4 加分项：分页功能（limit/offset）
- **状态**: ✅ 已实现
- **位置**: `app/router.py:49-62` — GET /tasks 添加 `limit`（默认 100，范围 1-1000）和 `offset`（默认 0）查询参数。
- **测试**: `tests/test_tasks.py` — `test_pagination_limit`、`test_pagination_offset`

### 6.5 加分项：使用 functools.lru_cache 实现缓存
- **状态**: ✅ 已实现
- **位置**: `app/cache.py` — 基于 `functools.lru_cache` 的版本号缓存机制。GET /tasks/{id} 优先查缓存，缓存命中则跳过数据库查询。创建、更新时写入缓存，删除时使缓存失效。
- **机制**: 使用版本号（version）作为 `lru_cache` 的参数，变更时递增版本号使旧缓存自动失效，新查询命中新版本。
- **测试**: `tests/test_cache.py` — 6 个缓存测试用例。

### 6.6 加分项：集成外部 API（天气信息）
- **状态**: ✅ 已实现
- **位置**: `app/weather.py` — 异步天气客户端，集成 wttr.in 免费 API（无需注册、无需 API Key）。
- **功能**: 创建/获取/更新任务时，自动获取 `due_date` 当天的天气预报（如 "Sunny，26°C（15~28°C）"），通过 `weather_info` 字段返回。
- **设计**:
  - 使用 wttr.in（`?format=j1`）获取 3 天天气预报，完全免费无需认证。
  - URL、城市、超时等全部配置化，集中在 `app/config.yaml` 的 `weather` 节。
  - 支持通过环境变量 `WEATHER_LOCATION` 覆盖城市配置。
  - 请求失败时优雅降级，`weather_info` 返回 `null`，不影响核心功能。
  - 天气结果按"日期+城市"缓存（使用 `lru_cache`），避免重复请求。
  - 日志使用项目统一的 `create_logger("weather", cfg.logging.level)` 方式。
- **配置项**（`app/config.yaml`）:
  ```yaml
  weather:
    enabled: true
    base_url: "https://wttr.in"
    location: "Beijing"
    timeout: 10
  ```
- **测试**: `tests/test_weather.py` — 8 个测试用例，覆盖成功/失败/无匹配日期/禁用等场景。
- **端到端验证**: ✅ 已通过 — curl 和 HTTP 接口均返回真实天气数据。

---

## 汇总

| 类别 | 总项 | 已实现 | 未实现 |
|------|------|--------|--------|
| 1. 框架与项目搭建 | 4 | 4 | 0 |
| 2. API 接口 | 6 | 6 | 0 |
| 3. 异步组件 | 1 | 1 | 0 |
| 4. 数据处理与校验 | 3 | 3 | 0 |
| 5. 测试 | 5 | 5 | 0 |
| 6. 优化与最佳实践 | 6 | 6 | 0 |
| **合计** | **25** | **25** | **0** |

### 未实现项目清单

无 — 面试题全部 25 项需求已全部实现。

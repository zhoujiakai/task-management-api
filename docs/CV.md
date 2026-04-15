# 面试备战手册 — Task Management API

> 本文档涵盖项目的全部设计思路、代码细节、技术要点和面试高频问题。只看这一份即可。

---

## 一、项目概述

一个基于 **FastAPI** 的任务管理 RESTful API，实现了完整的 CRUD 操作、异步通知、API Key 认证、Pydantic 数据校验、自定义异常处理、彩色日志和 YAML 配置管理。

**面试核心卖点：**
- FastAPI 异步框架 + SQLAlchemy 异步 ORM
- Pydantic v2 数据校验（自定义 field_validator）
- 依赖注入（DI）模式实现认证和数据库会话管理
- 自定义异常 + 全局异常处理器
- LRU 缓存层（版本号机制实现缓存失效）
- 列表接口分页支持（limit/offset）
- YAML + 环境变量双层配置管理
- 完善的异步测试体系（31 个测试，80% 覆盖率）
- 模块化分层架构（路由 → 缓存/服务 → 数据层）

---

## 二、技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI 0.115+ | 异步、自动 Swagger 文档、类型安全 |
| ASGI 服务器 | Uvicorn | 高性能异步服务器 |
| ORM | SQLAlchemy 2.0 (async) | 异步数据库操作 |
| 数据库 | SQLite (aiosqlite) | 零配置，开发用 |
| 数据校验 | Pydantic v2 | 请求/响应模型、自定义验证器 |
| 包管理 | uv + hatchling | 现代 Python 包管理，替代 pip+pip-tools |
| 测试 | pytest + pytest-asyncio + httpx | 异步测试，内存数据库隔离 |
| 代码风格 | Ruff | 替代 flake8 + black + isort |
| 日志 | colorama + logging | 彩色控制台日志 |
| 配置 | PyYAML + python-dotenv | YAML 配置文件 + 环境变量覆盖 |

---

## 三、目录结构与职责

```
task-management-api/
├── pyproject.toml          # 项目元数据、依赖、工具配置（唯一配置入口）
├── .python-version         # Python 版本锁定（3.12）
├── .env.example            # 环境变量模板（提交到 Git）
├── config.yaml             # 实际配置（gitignored，含密钥）
├── config.example.yaml     # 配置模板（提交到 Git）
├── logger.py               # 彩色日志模块
├── config.py               # YAML + 环境变量 配置管理模块
├── app/
│   ├── __init__.py
│   ├── main.py             # 应用入口：FastAPI 实例、lifespan、异常注册、路由挂载
│   ├── database.py         # 异步引擎、会话工厂、get_db 依赖、create_tables
│   ├── models.py           # ORM 模型（Task）+ 枚举（TaskStatus）
│   ├── schemas.py          # Pydantic 模型（TaskCreate/TaskUpdate/TaskResponse）
│   ├── router.py           # 5 个 CRUD 端点 + 认证 + 通知触发 + 缓存集成 + 分页
│   ├── cache.py            # LRU 缓存模块（版本号失效机制）
│   ├── exceptions.py       # 自定义异常类 + FastAPI 异常处理器注册
│   ├── auth.py             # API Key 认证依赖
│   └── notifications.py    # 异步模拟邮件通知
└── tests/
    ├── conftest.py          # 测试基础设施：内存 DB、依赖覆盖、认证 client
    ├── test_tasks.py        # CRUD 成功/失败 + 分页测试（12 个）
    ├── test_validation.py   # 数据校验测试（5 个）
    ├── test_notifications.py # 通知触发测试（3 个）
    ├── test_exceptions.py   # 异常响应格式测试（5 个）
    └── test_cache.py        # 缓存单元测试（6 个）
```

---

## 四、各模块详解

### 4.1 配置管理 — `config.py`

**设计思路：** 读取 YAML 文件 + 环境变量覆盖，将嵌套字典转为支持属性访问的对象（`cfg.database.url` 而非 `cfg["database"]["url"]`）。环境变量优先级高于 YAML，适合容器化部署时注入配置。

**核心实现：**

```python
from dotenv import load_dotenv
load_dotenv()

# 环境变量到配置键的映射
_ENV_OVERRIDES = {
    "DATABASE_URL": ("database", "url"),
    "API_KEY": ("auth", "api_key"),
    "SERVER_HOST": ("server", "host"),
    "SERVER_PORT": ("server", "port"),
    "LOG_LEVEL": ("logging", "level"),
}

class _Section:
    """嵌套配置节，dict → 对象属性"""
    def __init__(self, data: dict | None = None):
        for key, value in (data or {}).items():
            setattr(self, key, _Section(value) if isinstance(value, dict) else value)

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        with open(path) as f:
            data = yaml.safe_load(f) or {}

        # 应用环境变量覆盖
        for env_key, (section, field) in _ENV_OVERRIDES.items():
            env_value = os.environ.get(env_key)
            if env_value is not None:
                if section not in data:
                    data[section] = {}
                data[section][field] = env_value

        for key, value in data.items():
            setattr(self, key, _Section(value) if isinstance(value, dict) else value)

# 模块级单例，其他模块直接 from config import cfg
cfg = Config()
```

**面试要点：**
- `_Section` 是递归结构：遇到 dict 值就递归包装为 `_Section`，遇到标量值直接存储
- `config.yaml` 被 gitignore，`config.example.yaml` 作为模板提交；`.env` 同样被 gitignore，`.env.example` 作为模板
- `yaml.safe_load` 防止 YAML 反序列化攻击（不用 `yaml.load`）
- `load_dotenv()` 在模块导入时自动加载 `.env` 文件中的环境变量
- 环境变量覆盖机制：优先级 `.env` / 系统环境变量 > `config.yaml`，便于 Docker/K8s 部署时注入配置

**配置文件结构（config.yaml）：**

**环境变量模板（.env.example）：**
```bash
# 环境变量配置 — 复制此文件为 .env 并填写实际值
# 环境变量会覆盖 config.yaml 中的对应配置
# DATABASE_URL=sqlite+aiosqlite:///./tasks.db
# API_KEY=your-secret-api-key-here
# SERVER_HOST=0.0.0.0
# SERVER_PORT=8000
# LOG_LEVEL=INFO
```
```yaml
server:
  host: "0.0.0.0"
  port: 8000
database:
  url: "sqlite+aiosqlite:///./tasks.db"   # 异步 SQLite 连接串
auth:
  api_key: "test-api-key-123"              # API 认证密钥
notifications:
  enabled: true
  smtp_host: "smtp.example.com"
  smtp_port: 587
  sender: "noreply@example.com"
logging:
  level: "INFO"
```

---

### 4.2 彩色日志 — `logger.py`

**设计思路：** 继承 `logging.Formatter`，根据日志级别添加 colorama 颜色码。

```python
class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

def create_logger(name="app", level="INFO"):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not logger.handlers:   # 防止重复添加 handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColoredFormatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ))
        logger.addHandler(handler)
    return logger
```

**面试要点：**
- `init(autoreset=True)` — 每次输出后自动重置颜色，防止颜色"泄漏"到后续输出
- `if not logger.handlers` — 防止模块被多次导入时重复添加 handler
- `getattr(logging, level.upper(), logging.INFO)` — 安全地将字符串转为日志级别常量

---

### 4.3 缓存模块 — `app/cache.py`

**设计思路：** 使用 `functools.lru_cache` + 版本号机制实现单任务查询缓存。通过版本号递增使旧缓存自动失效，避免手动清除 `lru_cache` 内部条目。

**核心实现：**

```python
from functools import lru_cache

# 内部缓存存储（序列化后的任务数据）
_cache: dict[str, dict[str, Any]] = {}
# 版本号，用于缓存失效
_versions: dict[str, int] = {}

@lru_cache(maxsize=128)
def get_cached_task(task_id: str, version: int) -> dict[str, Any] | None:
    """通过 lru_cache 获取缓存的任务数据。version 参数变更时自动失效旧条目。"""
    return _cache.get(task_id)

def store_in_cache(task_id: str, data: dict[str, Any]) -> None:
    """将任务数据存入缓存，同时递增版本号。"""
    _cache[task_id] = data
    _versions[task_id] = _versions.get(task_id, 0) + 1

def invalidate_cache(task_id: str) -> None:
    """使缓存条目失效：删除数据并递增版本号。"""
    _cache.pop(task_id, None)
    _versions[task_id] = _versions.get(task_id, 0) + 1

def lookup(task_id: str) -> dict[str, Any] | None:
    """查找任务缓存：获取当前版本号后委托给 lru_cache。"""
    version = _versions.get(task_id, 0)
    return get_cached_task(task_id, version)
```

**面试要点：**
- **版本号机制**：`lru_cache` 基于参数做缓存键。`store_in_cache` 和 `invalidate_cache` 都会递增版本号，使得 `lookup` 传给 `get_cached_task` 的 `version` 参数变化，`lru_cache` 自动认为是新的调用，旧条目自然失效
- **为什么不用 TTL**：任务数据是强一致的，写操作后必须立即可见，TTL 只适合弱一致场景
- **为什么两层存储**：`_cache` 存实际数据，`lru_cache` 存查询结果（加速重复 lookup）。二者配合实现 O(1) 的缓存命中和失效
- **`clear_all()`** 调用 `get_cached_task.cache_clear()` 清空 `lru_cache` 统计信息，避免内存泄漏
- **maxsize=128**：最多缓存 128 个任务的查询结果，LRU 淘汰最久未访问的条目

---

### 4.4 数据库层 — `app/database.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config import cfg

# 异步引擎
engine = create_async_engine(cfg.database.url, echo=False)
# 会话工厂
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：yield 一个数据库会话，请求结束自动关闭"""
    async with async_session() as session:
        yield session

async def create_tables() -> None:
    """启动时建表（lifespan 中调用）"""
    from app.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

**面试要点：**
- `create_async_engine` — 异步版本的引擎，连接串格式 `sqlite+aiosqlite:///./tasks.db`
- `async_sessionmaker` — 工厂模式创建会话，`expire_on_commit=False` 避免 commit 后访问属性触发延迟加载
- `get_db` 使用 `yield` 模式 — FastAPI 的依赖注入支持生成器，yield 前是 setup，yield 后是 teardown
- `engine.begin()` — 获取一个事务连接，`run_sync` 在异步上下文中执行同步的 `create_all`
- 为什么用 `yield` 而不是 `return`？因为需要在请求结束后关闭 session（`async with` 的 `__aexit__`）

---

### 4.5 ORM 模型 — `app/models.py`

```python
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

**面试要点：**
- `Mapped[str]` — SQLAlchemy 2.0 的类型注解写法，替代传统的 `Column(String(200))`
- `TaskStatus(str, enum.Enum)` — 继承 str 使其可序列化，用于 JSON 响应和数据库存储
- `default=lambda: str(uuid.uuid4())` — 用 lambda 延迟求值，每次生成新的 UUID
- `server_default=func.now()` — 数据库层面的默认值（SQL 的 `NOW()`），而非 Python 层
- `onupdate=func.now()` — 每次 UPDATE 时自动更新时间戳
- `id` 用 UUID 字符串而非自增整数 — 分布式友好，不暴露数据量

---

### 4.6 Pydantic 校验 — `app/schemas.py`

```python
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    status: str = "pending"
    due_date: datetime | None = None

    @field_validator("due_date")
    @classmethod
    def due_date_must_be_future(cls, v: datetime | None) -> datetime | None:
        if v is not None and v <= datetime.now(tz=v.tzinfo):
            raise ValueError("due_date must be in the future")
        return v

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v: str) -> str:
        allowed = [s.value for s in TaskStatus]
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v

class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = None
    due_date: datetime | None = None
    # 同样有 field_validator

class TaskResponse(BaseModel):
    id: str
    title: str
    description: str | None
    status: str
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}   # 允许从 ORM 对象直接转换
```

**面试要点：**
- `Field(...)` — `...` 表示必填；`Field(None)` 表示可选，默认 None
- `@field_validator` — Pydantic v2 的验证器写法（v1 是 `@validator`）
- `model_dump(exclude_unset=True)` — 只导出用户实际设置的字段，未设置的字段不包含，用于 PATCH 语义的部分更新
- `from_attributes = True` — Pydantic v2 的写法（v1 是 `orm_mode = True`），允许从 ORM 对象的属性读取数据
- `datetime.now(tz=v.tzinfo)` — 使用请求中携带的时区进行比较，而非服务器本地时区

**三个 Schema 的区别：**

| Schema | 用途 | 特点 |
|--------|------|------|
| `TaskCreate` | POST 请求体 | title 必填，status 默认 pending |
| `TaskUpdate` | PUT 请求体 | 所有字段可选，支持部分更新 |
| `TaskResponse` | 所有接口的响应 | 包含 id、created_at、updated_at 等只读字段 |

---

### 4.7 认证 — `app/auth.py`

```python
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from config import cfg

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key != cfg.auth.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
```

**面试要点：**
- `APIKeyHeader` — 从请求头提取 API Key，`auto_error=False` 让我们自己控制错误响应
- `Security()` — FastAPI 的安全依赖声明，和 `Depends()` 类似但会在 Swagger 中显示锁图标
- 认证逻辑：从 header 取值 → 与配置中的 key 比较 → 不匹配则 401
- 在 router 上通过 `dependencies=[Depends(verify_api_key)]` 全局生效，所有端点自动受保护

---

### 4.8 自定义异常 — `app/exceptions.py`

```python
class TaskNotFoundException(Exception):
    def __init__(self, task_id: str):
        self.task_id = task_id

class ValidationException(Exception):
    def __init__(self, detail: str):
        self.detail = detail

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(TaskNotFoundException)
    async def task_not_found_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": f"Task with id '{exc.task_id}' not found"})

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": exc.detail})
```

**面试要点：**
- `@app.exception_handler(CustomException)` — FastAPI 的全局异常处理机制
- 当路由中 `raise TaskNotFoundException(id)` 时，FastAPI 自动调用对应的 handler
- 统一错误格式 `{"detail": "..."}` — 与 FastAPI 内置的 HTTPException 格式一致
- 为什么不用 `HTTPException`？自定义异常可以在业务层抛出，与 HTTP 层解耦；handler 负责映射为 HTTP 状态码

---

### 4.9 异步通知 — `app/notifications.py`

```python
async def send_notification(task_id: str, title: str, status: str) -> None:
    log.info(f"Sending notification: task '{title}' ({task_id}) changed to '{status}'")
    await asyncio.sleep(0.01)  # 模拟网络延迟
    log.info(f"Notification sent for task {task_id}")
```

**面试要点：**
- 用 `await asyncio.sleep()` 模拟 I/O 操作（真实场景连接 SMTP / 消息队列）
- 在 `router.py` 中 `await send_notification(...)` — 当前是 await，也可以用 `background_tasks.add_task()` 实现真正的后台执行
- 触发条件：仅在 `status` 从非 completed 变为 completed 时触发，防止重复通知

---

### 4.10 路由层 — `app/router.py`

**5 个端点的完整流程：**

```
POST   /tasks         → 校验请求体(TaskCreate) → 创建 ORM 对象 → db.add → commit → refresh → 写入缓存 → 返回
GET    /tasks         → select(Task) → 可选 status 过滤 + 分页(limit/offset) → 按创建时间倒序 → 返回列表
GET    /tasks/{id}    → 查缓存 → 命中则直接返回 → 未命中则 db.get → 写入缓存 → 返回
PUT    /tasks/{id}    → db.get → 记录 old_status → model_dump(exclude_unset) 更新字段 → commit → 更新缓存 → 检测状态变更 → 触发通知 → 返回
DELETE /tasks/{id}    → db.get → db.delete → commit → 使缓存失效 → 204
```

**关键代码片段 — 缓存集成的获取任务：**

```python
@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)) -> Task:
    """通过 ID 获取指定任务（带缓存）。"""
    # 先查缓存
    cached = lookup(task_id)
    if cached is not None:
        return cached

    # 缓存未命中，查数据库
    task = await db.get(Task, task_id)
    if task is None:
        raise TaskNotFoundException(task_id)
    store_in_cache(task.id, _serialize_task(task))
    return task
```

**关键代码片段 — 分页支持的列表查询：**

```python
@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[Task]:
    stmt = select(Task)
    if status is not None:
        stmt = stmt.where(Task.status == TaskStatus(status))
    stmt = stmt.order_by(Task.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
```

**关键代码片段 — 更新任务：**

```python
@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_in: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if task is None:
        raise TaskNotFoundException(task_id)

    update_data = task_in.model_dump(exclude_unset=True)  # 只包含用户设置的字段
    old_status = task.status

    # 逐字段更新
    for field in ("title", "description", "status", "due_date"):
        if field in update_data:
            if field == "status":
                setattr(task, field, TaskStatus(update_data[field]))
            else:
                setattr(task, field, update_data[field])

    await db.commit()
    await db.refresh(task)

    # 更新缓存
    store_in_cache(task.id, _serialize_task(task))

    # 状态从非完成 → 完成：触发通知
    if task.status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
        await send_notification(task.id, task.title, task.status.value)

    return task
```

**面试要点：**
- **缓存一致性**：创建后 `store_in_cache`、更新后 `store_in_cache`、删除后 `invalidate_cache`，保证读缓存与数据库一致
- **`_serialize_task()`**：将 ORM 对象转为纯字典（含 `isoformat()` 序列化日期），因为 ORM 对象在 session 关闭后无法访问延迟加载属性
- **分页参数**：`Query(100, ge=1, le=1000)` 设置默认值和范围约束，防止一次返回过多数据
- `model_dump(exclude_unset=True)` — Pydantic v2 方法，只导出请求中实际传入的字段，实现 PATCH 语义
- `db.refresh(task)` — commit 后从数据库重新读取，获取 server_default 生成的值（如 updated_at）
- 认证通过 `dependencies=[Depends(verify_api_key)]` 声明在 router 级别，所有端点自动生效
- `response_model=TaskResponse` — FastAPI 自动将 ORM 对象转为 JSON，并在 Swagger 中展示响应结构

---

### 4.11 应用入口 — `app/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting Task Management API")
    await create_tables()    # 启动时建表
    yield                    # 应用运行中...
    log.info("Shutting down Task Management API")

app = FastAPI(title="Task Management API", lifespan=lifespan)
register_exception_handlers(app)    # 注册自定义异常处理器
app.include_router(router)          # 挂载路由

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

**面试要点：**
- `lifespan` — FastAPI 的生命周期管理（替代旧版 `@app.on_event("startup")`），yield 前是 startup，yield 后是 shutdown
- `register_exception_handlers` — 在路由挂载前注册，确保所有请求都能捕获自定义异常
- `app.include_router(router)` — 将路由模块注册到应用，router 中定义的 prefix 和 tags 自动生效
- `/health` — 健康检查端点，不经过认证（定义在 router 外）

---

## 五、测试体系详解

### 5.1 测试基础设施 — `conftest.py`

```python
# 内存数据库（每个测试独立）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# 每个测试前后：建表 → 运行测试 → 删表
@pytest.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 覆盖真实数据库依赖
app.dependency_overrides[get_db] = override_get_db

# 异步 HTTP 客户端（不启动真实服务器）
@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# 预创建一个任务的 fixture
@pytest.fixture
async def sample_task(client, api_headers):
    due = datetime.now(timezone.utc) + timedelta(days=7)
    response = await client.post("/tasks", json={...}, headers=api_headers)
    return response.json()
```

**面试要点：**
- 内存数据库 `:memory:` — 每个测试完全隔离，无副作用
- `autouse=True` — 每个测试自动执行，不需要手动声明
- `app.dependency_overrides[get_db] = override_get_db` — FastAPI 的依赖覆盖机制，用内存 DB 替换真实 DB
- `ASGITransport` — httpx 直接调用 ASGI 应用，不启动真实 HTTP 服务器，测试更快
- 认证不做覆盖（保留真实认证），测试无 Key 访问时返回 401，测试有 Key 时传 `api_headers`

### 5.2 测试分类（31 个测试）

**test_tasks.py（12 个）— CRUD 成功/失败 + 分页：**
- 创建任务、列表查询、状态过滤、获取单个、更新、删除
- 获取/删除/更新不存在的任务 → 404
- 健康检查、未认证访问 → 401
- 分页 limit 参数限制返回数量
- 分页 offset 参数跳过前 N 条

**test_cache.py（6 个）— 缓存单元测试：**
- 基本的缓存存取
- 缓存未命中返回 None
- 缓存失效后不再返回旧数据
- store 更新后返回新数据
- 清空全部缓存
- lru_cache 装饰器被正确使用

**test_validation.py（5 个）— 数据校验：**
- 空标题 → 422
- 过去的 due_date → 422
- 无效 status → 422
- 更新时传过去的日期 → 422
- 有效的未来日期 → 201（正向测试）

**test_notifications.py（3 个）— 通知触发：**
- 完成 → 触发通知
- 改为 in_progress → 不触发
- 已完成的任务再更新 → 不重复触发

**test_exceptions.py（5 个）— 异常响应格式：**
- 404 响应包含 `detail` 字段且包含任务 ID
- 401 响应格式验证
- 422 响应格式验证

### 5.3 运行命令

```bash
uv sync --extra dev                        # 安装开发依赖
uv run pytest --cov=app tests/             # 运行测试 + 覆盖率
uv run ruff check .                        # 代码风格检查
```

---

## 六、核心设计模式总结

### 6.1 依赖注入（Dependency Injection）

FastAPI 的 `Depends()` 是整个架构的核心粘合剂：

```
请求 → router（Depends(verify_api_key)）→ Depends(get_db) → 业务逻辑
              ↓ 认证检查                        ↓ 数据库会话
         401 未授权                      yield session → 请求结束自动关闭
```

- 认证：`dependencies=[Depends(verify_api_key)]` 在 router 级别声明，全局生效
- 数据库：每个端点 `db: AsyncSession = Depends(get_db)` 获取独立会话

### 6.2 缓存策略

```
GET /tasks/{id} 请求流程：
  → lookup(task_id) 查缓存
  → 命中 → 直接返回（不经过数据库）
  → 未命中 → db.get() → store_in_cache() → 返回

写操作缓存一致性：
  POST   → commit → store_in_cache()   # 写入缓存
  PUT    → commit → store_in_cache()   # 更新缓存
  DELETE → commit → invalidate_cache() # 删除缓存
```

- 使用版本号机制：每次写操作递增版本号，`lru_cache` 因参数变化自动失效旧条目
- 不用 TTL：任务数据要求强一致，写后必须立即可见

### 6.3 分层架构

```
router.py（HTTP 层）→ schemas.py（校验层）→ models.py（数据层）→ database.py（引擎层）
      ↓                    ↓
auth.py（认证）      exceptions.py（异常）
      ↓
notifications.py（异步通知）
```

### 6.4 请求处理流程

```
Client → Uvicorn → FastAPI
  → 认证检查（verify_api_key）
  → Pydantic 校验（TaskCreate/TaskUpdate）
  → 路由处理函数
    → 缓存查询（lookup，仅 GET 单条）
    → 数据库操作（AsyncSession）
    → 缓存更新/失效（store_in_cache / invalidate_cache）
    → 异常处理（TaskNotFoundException → 404）
    → 异步通知（send_notification）
  → Pydantic 序列化（TaskResponse）
  → JSON 响应
```

---

## 七、面试高频问题与回答

### Q1: 为什么选择 FastAPI 而不是 Flask/Django？

FastAPI 基于 ASGI，原生支持 async/await，在高并发 I/O 场景下性能远超 Flask（WSGI）。内置 Swagger 文档、Pydantic 类型校验和依赖注入系统，减少了大量样板代码。相比 Django，FastAPI 更轻量，适合微服务和 API-only 项目。

### Q2: SQLAlchemy 异步和同步有什么区别？

同步使用 `Session`，每个操作阻塞当前线程。异步使用 `AsyncSession` + `create_async_engine`，所有数据库操作都是 `await` 的，不会阻塞事件循环。本项目中 `get_db()` 用 `async with` 管理会话生命周期，`db.commit()` 和 `db.refresh()` 都是异步调用。

### Q3: Pydantic 的 `model_dump(exclude_unset=True)` 有什么用？

它只导出用户在请求中实际传入的字段。例如用户只传了 `{"title": "新标题"}`，那么 `exclude_unset=True` 后只会得到 `{"title": "新标题"}`，`description` 和 `status` 不会被包含（它们的值是 None 是因为默认值，不是用户设置的）。这实现了 PATCH 语义的部分更新。

### Q4: 如何保证测试之间互不影响？

三个层面的隔离：
1. **数据库隔离**：使用 SQLite 内存数据库 `:memory:`，每个测试前建表、后删表（`autouse=True` fixture）
2. **依赖覆盖**：`app.dependency_overrides[get_db]` 将真实数据库替换为内存数据库
3. **HTTP 隔离**：使用 httpx 的 `ASGITransport` 直接调用 ASGI 应用，不启动真实服务器

### Q5: 认证是怎么实现的？如何扩展为 JWT？

当前用 API Key Header 认证：从 `X-API-Key` 请求头取值，与配置中的密钥比较。通过 `APIKeyHeader + Security()` 声明，在 router 上用 `dependencies=[Depends(verify_api_key)]` 全局生效。

扩展为 JWT：将 `APIKeyHeader` 替换为 `OAuth2PasswordBearer`，在 `verify_token` 依赖中用 `jose` 库解码 JWT，验证签名和过期时间。

### Q6: 为什么 Task 的 id 用 UUID 而不是自增整数？

- 分布式友好：多个服务实例可以独立生成 ID，无需协调
- 安全性：不暴露数据量和创建顺序
- 迁移方便：合并不同数据库的数据时不会 ID 冲突
- REST API 最佳实践：使用 UUID 作为资源标识符

### Q7: 通知为什么只在状态变为 completed 时触发？

通过记录 `old_status`，在更新后对比判断：`task.status == COMPLETED and old_status != COMPLETED`。这确保只在"首次完成"时触发通知，避免重复编辑已完成的任务时反复发送。这是事件驱动设计中的"状态变更检测"模式。

### Q8: lifespan 和 on_event 有什么区别？

`@app.on_event("startup"/"shutdown")` 是旧版 API，已在 FastAPI 新版本中标记为废弃。`lifespan` 使用 async context manager（`@asynccontextmanager`），yield 前是启动逻辑，yield 后是关闭逻辑，代码更紧凑，资源管理更清晰，还能在 lifespan 中传递状态对象。

### Q9: 如果要部署到生产环境，需要改什么？

1. **数据库**：SQLite → PostgreSQL（`asyncpg` 驱动），连接串改为 `postgresql+asyncpg://...`
2. **认证**：API Key → JWT / OAuth2
3. **通知**：模拟 → 真实 SMTP 或消息队列（RabbitMQ/Kafka）
4. **配置**：YAML + `.env` → 结合 `pydantic-settings` 的 `BaseSettings` 做更严格的类型校验
5. **部署**：Uvicorn + Gunicorn 进程管理，或 Docker 容器化
6. **日志**：控制台 → 文件/ELK/Loki
7. **缓存**：进程内 LRU → Redis/Memcached（分布式缓存，支持多实例共享）

### Q10: 缓存是如何实现的？为什么用版本号而不是 TTL？

使用 `functools.lru_cache` + 版本号机制。`lru_cache` 基于函数参数做缓存，当版本号变化时，`lru_cache` 认为是新的调用，旧条目自然失效。不用 TTL 的原因：任务数据要求强一致性，写操作后必须立即可见，TTL 只适合弱一致场景（如排行榜、计数器）。版本号机制确保了写后读（read-after-write）的一致性。

### Q11: 分页是怎么实现的？有哪些参数校验？

列表接口 `GET /tasks` 新增 `limit` 和 `offset` 查询参数。`limit` 默认 100，范围 1~1000（`Query(100, ge=1, le=1000)`）；`offset` 默认 0，最小 0（`Query(0, ge=0)`）。SQLAlchemy 通过 `.offset(offset).limit(limit)` 实现，对应 SQL 的 `OFFSET ... LIMIT ...`。FastAPI 的 `Query()` 自动在 Swagger 文档中展示参数约束，非法值返回 422。

### Q12: 环境变量覆盖 YAML 配置是怎么实现的？

在 `Config.__init__` 中，先用 `yaml.safe_load` 加载 YAML 数据，然后遍历 `_ENV_OVERRIDES` 映射表，检查对应的环境变量是否存在。如果存在，就用环境变量的值覆盖 YAML 中的配置。通过 `python-dotenv` 的 `load_dotenv()` 在模块导入时自动加载 `.env` 文件。这种设计遵循了 12-Factor App 原则，配置优先级为：系统环境变量 > `.env` 文件 > `config.yaml`。

### Q13: 项目中用了哪些 Python 3.10+ 的新特性？

- `str | None` 类型注解（PEP 604，联合类型语法），替代 `Optional[str]`
- `asyncio` 在标准库中的持续改进
- `match/case`（本项目未使用，但了解即可）
- `TypeAlias`（PEP 613，本项目未使用）

---

## 八、pyproject.toml 关键配置

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "task-management-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",      # [standard] 包含 uvloop、watchfiles 等性能组件
    "sqlalchemy[asyncio]>=2.0.0",     # [asyncio] 包含异步扩展
    "aiosqlite>=0.20.0",              # SQLite 异步驱动
    "pyyaml>=6.0",                    # YAML 解析
    "colorama>=0.4.6",                # 终端颜色
    "pydantic>=2.0.0",                # 数据校验
    "python-dotenv>=1.2.2",           # 环境变量管理（.env 文件支持）
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",                  # 测试框架
    "pytest-asyncio>=0.24.0",         # 异步测试支持
    "httpx>=0.27.0",                  # 异步 HTTP 客户端（测试用）
    "pytest-cov>=5.0.0",              # 覆盖率
    "ruff>=0.6.0",                    # 代码检查 + 格式化
]

[tool.hatch.build.targets.wheel]
packages = ["app"]                     # 告诉 hatchling 打包 app 目录

[tool.pytest.ini_options]
asyncio_mode = "auto"                  # 自动识别 async 测试函数

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "W"]         # E=错误 F=pyflakes I=import排序 W=警告
```

**面试要点：**
- `hatchling` — 现代 Python 构建后端，替代 `setuptools`
- `uvicorn[standard]` — 方括号是 extras，额外安装 uvloop（高性能事件循环）和 watchfiles（热重载）
- `sqlalchemy[asyncio]` — 安装异步扩展
- `asyncio_mode = "auto"` — pytest-asyncio 自动模式，不需要每个测试都加 `@pytest.mark.asyncio`（但我们加了，更显式）
- dev 依赖用 `--extra dev` 安装：`uv sync --extra dev`

---

## 九、依赖安装方式

```bash
# 基础依赖（运行项目）
uv sync

# 开发依赖（测试 + lint）
uv sync --extra dev

# 或者一步到位
uv sync --all-extras
```

**为什么用 uv？** uv 是 Rust 编写的 Python 包管理器，比 pip 快 10-100 倍，内置虚拟环境管理，lockfile 保证可重复构建。

---

## 十、快速启动流程

```bash
# 1. 进入项目目录
cd task-management-api

# 2. 安装所有依赖（含开发依赖）
uv sync --extra dev

# 3. 确保配置文件存在（已有 config.yaml，或从模板复制）
cp config.example.yaml config.yaml
cp .env.example .env                    # 可选：使用环境变量覆盖配置

# 4. 启动服务
uv run uvicorn app.main:app --reload

# 5. 访问 Swagger 文档
# 浏览器打开 http://localhost:8000/docs

# 6. 测试 API（需要认证）
curl -X POST http://localhost:8000/tasks \
  -H "X-API-Key: test-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{"title":"我的第一个任务"}'

# 7. 运行测试
uv run pytest --cov=app tests/

# 8. 代码检查
uv run ruff check .
```

---

## 十一、覆盖率报告

```
Name                   Stmts   Miss  Cover
------------------------------------------
app/__init__.py            0      0   100%
app/auth.py                8      0   100%
app/cache.py              20      0   100%
app/database.py           12      5    58%
app/exceptions.py         15      2    87%
app/main.py               21      4    81%
app/models.py             20      0   100%
app/notifications.py       7      0   100%
app/router.py             71     32    55%
app/schemas.py            51      3    94%
------------------------------------------
TOTAL                    225     46    80%
```

- 31 个测试全部通过
- 总覆盖率 80%（超过 70% 要求）
- auth、cache、models、notifications 达到 100%
- router 和 database 覆盖率较低是因为部分启动/关闭路径在单元测试中不会执行

---

*文档最后更新：2026-04-15（同步至 commit 5eddb83）*

# Task: Build a Task Management API

## Task Description

Develop a RESTful API for a task management system. The API should allow users to create, read, update, and delete tasks, with asynchronous notifications for completions. Use Python 3.10+ and focus on clean, production-ready code.

## Time Allocation Suggestion

- **20 minutes**: Planning and setup (virtual env, dependencies).
- **60 minutes**: Core implementation (endpoints, DB integration).
- **30 minutes**: Async features and testing.
- **10 minutes**: Documentation and cleanup.

## Detailed Requirements

### 1. Framework and Setup

- Use **FastAPI** for its built-in async support, automatic docs (via Swagger), and type safety.
- Install dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pytest`, `asyncio` (built-in).
- **Database**: SQLite for simplicity—no external setup needed. Use SQLAlchemy ORM to define a `Task` model with columns:
  - `id` (int, primary key)
  - `title` (str)
  - `description` (str, optional)
  - `status` (enum: `'pending'`, `'completed'`)
  - `due_date` (datetime)

### 2. API Endpoints

- **POST /tasks**: Create a new task. Request body: JSON with `title`, `description`, `due_date`. Return the created task with ID.
- **GET /tasks**: List all tasks, with optional query params for filtering (e.g., `?status=pending`).
- **GET /tasks/{id}**: Retrieve a single task.
- **PUT /tasks/{id}**: Update a task (e.g., mark as completed). If status changes to `'completed'`, trigger an async notification.
- **DELETE /tasks/{id}**: Remove a task.
- Implement rate limiting or basic auth (e.g., via `fastapi.security` with API keys) to prevent abuse.

### 3. Asynchronous Component

- Use `asyncio` to create a background task for sending a mock email on completion (e.g., print to console or log: `"Email sent for task {id}"`).

### 4. Data Handling and Validation

- Use **Pydantic** models for request/response schemas to enforce types and validation (e.g., `due_date` must be future).
- Handle errors gracefully: Custom exceptions for not-found tasks, validation failures (return 400/404 with messages).

### 5. Testing

- Write **pytest** tests for:
  - Successful task creation and retrieval.
  - Async notification trigger.
  - Error cases (e.g., invalid date).
- Aim for **70%+ coverage** to demonstrate TDD awareness.

### 6. Optimizations and Best Practices

- Use environment variables for configs (e.g., via `dotenv`).
- Implement logging with `logging` module.
- Ensure thread-safety for DB access in async contexts.
- **Bonus extensions** (if time): Add pagination (e.g., `limit`/`offset`), caching with `functools.lru_cache`, or integration with an external API (e.g., fetch weather for `due_date` via `requests` to a free endpoint like OpenWeather).

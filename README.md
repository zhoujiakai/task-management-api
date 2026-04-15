# Task Management API

A RESTful task management API built with FastAPI, featuring CRUD operations, async notifications, API key authentication, and comprehensive test coverage.

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and edit config
cp config.example.yaml config.yaml

# Run the server
uv run uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive Swagger documentation.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tasks` | Create a new task |
| GET | `/tasks` | List all tasks (with optional status filter) |
| GET | `/tasks/{id}` | Get a specific task |
| PUT | `/tasks/{id}` | Update a task |
| DELETE | `/tasks/{id}` | Delete a task |

All endpoints require an `X-API-Key` header for authentication.

## Testing

```bash
# Run tests with coverage
uv run pytest --cov=app tests/

# Lint
uv run ruff check .
```

## Configuration

Copy `config.example.yaml` to `config.yaml` and adjust settings:

- `server` - Host and port
- `database` - SQLAlchemy async connection URL
- `auth.api_key` - API key for authentication
- `notifications` - Email notification settings
- `logging.level` - Log level (DEBUG, INFO, WARNING, ERROR)

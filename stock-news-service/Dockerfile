FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

COPY pyproject.toml uv.lock ./

# Install dependencies (no dev group)
RUN uv sync --no-dev --frozen

COPY . .

# Default: run the FastAPI server
# Override CMD to run the cron job: python cron.py
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

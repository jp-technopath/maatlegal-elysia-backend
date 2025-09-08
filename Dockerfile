FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY . /app
RUN python -m pip install -U pip && python -m pip install -e .
CMD ["/bin/sh","-lc","elysia start --host 0.0.0.0 --port ${PORT:-8000}"]
FROM python:3.13-slim

# git is needed to fetch the pylinac fork pinned in requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Install dependencies first so code changes don't invalidate this layer
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY .streamlit ./.streamlit
COPY app.py ./

RUN useradd --create-home appuser
USER appuser

EXPOSE 8505

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8505/_stcore/health')"

# Run Streamlit directly (not via main.py) so it is PID 1 and receives SIGTERM on `docker stop`
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8505", "--server.headless=true"]

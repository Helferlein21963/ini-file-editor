# ── Stage 1: build ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# System dependencies for Qt (headless / build-time only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb libgl1 libglib2.0-0 libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

# Run tests headlessly
RUN xvfb-run --auto-servernum pytest tests/ -v

# Build distribution
RUN pip install build && python -m build

# ── Stage 2: runtime image ────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="Helferlein21963"
LABEL description="ini-file-editor – headless export mode"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

COPY example.ini /app/

# In headless mode the app can be imported and used as a library
# The GUI entrypoint requires a display (e.g. via xvfb or X11 forwarding)
ENTRYPOINT ["python", "-c", "from ini_parser import IniParser, SortMode, ExportFormat; \
    import sys; \
    doc = IniParser.parse_file(sys.argv[1]); \
    print(doc.sorted_copy(SortMode.SECTIONS_AND_KEYS_ALPHA).export(ExportFormat[sys.argv[2].upper()]))"]
CMD ["/app/example.ini", "json"]

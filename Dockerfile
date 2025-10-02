FROM arm64v8/alpine:latest AS builder

RUN apk add --no-cache \
    python3 \
    py3-pip \
    build-base \
    python3-dev \
    gcc \
    musl-dev

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install asammdf numpy requests

# Runtime stage
FROM arm64v8/alpine:latest

RUN apk add --no-cache python3

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY cansender.py .

# Copy dataset
COPY mercedes.mf4 .

CMD ["python3", "cansender.py"]

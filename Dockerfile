FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd --create-home --uid 10001 cab
WORKDIR /opt/cab

COPY pyproject.toml constraints.txt README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir --constraint constraints.txt .

USER cab
ENTRYPOINT ["cab"]
CMD ["--help"]

FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY examples ./examples
RUN useradd --create-home app
USER app
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["resume-cli"]
CMD ["--help"]

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app/src:/app
RUN useradd --create-home fabsight && chown -R fabsight:fabsight /app
USER fabsight
CMD ["python","scripts/run_api.py"]

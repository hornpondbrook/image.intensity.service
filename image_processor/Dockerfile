FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src
COPY image_processor/ /app/image_processor

EXPOSE 50051

CMD ["python", "-m", "image_processor.server"]

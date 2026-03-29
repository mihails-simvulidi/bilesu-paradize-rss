FROM python
WORKDIR /app
RUN apt-get update && \
    apt-get install --no-install-recommends -y curl && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
EXPOSE 80
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]

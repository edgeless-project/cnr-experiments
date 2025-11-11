FROM ultralytics/ultralytics:latest-jetson-jetpack5

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir flask waitress

EXPOSE 5000
CMD ["python3", "index.py"]

FROM python:3

ENV LOG_LEVEL=INFO
ENV PORT=7101
ENV MAX_WORKERS=10

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $PORT

CMD python ./src/function.py --log-level $LOG_LEVEL --port $PORT --max-workers $MAX_WORKERS

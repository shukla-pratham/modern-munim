import multiprocessing
import os

workers = int(os.getenv("GUNICORN_WORKERS", "2"))
if workers < 2:
    workers = 2
if workers > 4:
    workers = 4

worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
graceful_timeout = 30
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
capture_output = True

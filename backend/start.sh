#!/bin/bash

echo "====== Starting: gunicorn"
gunicorn -k "uvicorn.workers.UvicornWorker" -c "/gunicorn_conf.py" --capture-output "app.main:app"

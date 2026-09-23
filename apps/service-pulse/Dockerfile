FROM python:3.12-slim

WORKDIR /app
COPY main.py index.html board.js board.css ./

USER 10001:10001
EXPOSE 8080
CMD ["python", "-u", "main.py"]

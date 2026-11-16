FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

WORKDIR /app
COPY main.py index.html board.js board.css ./

USER 10001:10001
EXPOSE 8080
CMD ["python", "-u", "main.py"]

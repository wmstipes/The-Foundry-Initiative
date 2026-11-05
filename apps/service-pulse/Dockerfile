FROM python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54

WORKDIR /app
COPY main.py index.html board.js board.css ./

USER 10001:10001
EXPOSE 8080
CMD ["python", "-u", "main.py"]

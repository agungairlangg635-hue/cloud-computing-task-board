FROM python:3.12-slim
WORKDIR /app
COPY app.py /app/app.py
RUN mkdir -p /var/lib/backend_data && useradd --create-home appuser && chown -R appuser:appuser /app /var/lib/backend_data
USER appuser
EXPOSE 5000
CMD ["python", "-u", "app.py"]

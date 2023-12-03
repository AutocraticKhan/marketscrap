FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY script.py .

# Make port 80 available to the world outside this container
EXPOSE 80

CMD ["python", "script.py"]

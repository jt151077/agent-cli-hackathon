FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Expose the port Cloud Run uses
ENV PORT=8080
EXPOSE 8080

# Start the server using uvicorn pointing to the Starlette app
CMD ["uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8080"]
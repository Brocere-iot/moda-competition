# 1. Use an official lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first (helps with Docker caching)
COPY requirements.txt .

# 4. Install the dependencies
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

# 5. Copy the rest of your application code into the container
COPY . .

# 6. Expose the port FastAPI will run on
EXPOSE 8000

# 7. Command to run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
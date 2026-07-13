# 1. Use an official lightweight Python image
FROM python:3.11-slim

# MODA COMPLIANCE FIX: Create a dedicated non-root group and user
# We use a explicit UID/GID (10001) to keep permissions clean
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /bin/sbin/nologin appuser

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first (helps with Docker caching)
COPY requirements.txt .

# 4. Install the dependencies
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

# 5. Copy the rest of your application code into the container
COPY . .

# MODA COMPLIANCE FIX: Explicitly grant the appuser ownership over the directory
RUN chown -R appuser:appgroup /app

# 6. Expose the port FastAPI will run on
EXPOSE 8000

# MODA COMPLIANCE FIX: Drop privileges and switch to the low-privilege user
USER appuser

# 7. Command to run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
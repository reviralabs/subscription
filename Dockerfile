# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV LEMON_SQUEEZY_API_KEY=your_actual_key_here
ENV FIREBASE_PROJECT_ID=your_actual_project_id_here
ENV LEMON_SQUEEZY_WEBHOOK_SECRET=your_actual_secret_here
ENV DATABASE_URL=sqlite:///./subscriptions.db

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
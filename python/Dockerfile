# Use the official Python image from the Docker Hub
FROM python:3.13.1-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install  -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Specify the command to run the application
CMD ["python", "app.py"]
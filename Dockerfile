# Use the official Python base image
FROM python:latest

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5005

# Run app.py when the container launches
CMD ["python", "main.py"]

# Docker Image run command
# docker run -d --name medcare-mailgun-container -p 5005:5005 medcare-mailgun
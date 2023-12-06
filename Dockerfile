# Use the official Python image as the base image
FROM python:3.12

# Install required system dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory inside the container
WORKDIR /scripts

# Copy the local scripts to the container
COPY . /scripts

# Install Python libraries
RUN pip install requests telebot yt-dlp mega.py

# Specify additional libraries
RUN pip install configparser

# Upgrade tenacity to version 7.0.0
RUN pip install --upgrade tenacity==7.0.0

# Create a folder called "downloads"
RUN mkdir -p downloads

# Execute "bla.py" when the container starts
CMD ["python", "bot_youtube.py"]

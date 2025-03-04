# Use the official Alpine image from the Docker Hub
FROM alpine:latest

# Install necessary packages
RUN apk add --no-cache g++ cmake ninja

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Build the project
RUN cmake . -G Ninja && ninja

# Set the entrypoint to the built executable
CMD ["./Hex"]
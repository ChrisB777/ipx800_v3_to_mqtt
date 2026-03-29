#!/bin/bash
# Deploy IPX800 v3 to MQTT Bridge to Docker Hub

set -e

VERSION="v1.0.0"
IMAGE_NAME="chrisb777/ipx800_v3_to_mqtt"

echo "=== Deploying to Docker Hub ==="
echo "Image: $IMAGE_NAME"
echo "Version: $VERSION"
echo ""

# Check if logged in
echo "Checking Docker Hub login..."
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo "Please login to Docker Hub first:"
    echo "  docker login"
    exit 1
fi

# Build image
echo "Building image..."
docker build -t $IMAGE_NAME:$VERSION -t $IMAGE_NAME:latest .

# Push images
echo "Pushing version tag..."
docker push $IMAGE_NAME:$VERSION

echo "Pushing latest tag..."
docker push $IMAGE_NAME:latest

echo ""
echo "=== Deployed successfully! ==="
echo ""
echo "Pull command:"
echo "  docker pull $IMAGE_NAME:$VERSION"
echo ""
echo "Or use in docker-compose:"
echo "  image: $IMAGE_NAME:$VERSION"

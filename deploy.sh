#!/bin/bash

set -e

echo "🚀 Deploying TaskFlow..."

echo "📥 Pulling latest code..."
git pull origin main

echo "🐳 Rebuilding and starting containers..."
docker compose up -d --build

echo "🩺 Checking application health..."
sleep 5

if curl -fs http://localhost/health > /dev/null; then
    echo "✅ TaskFlow is healthy!"
else
    echo "❌ Health check failed!"
    exit 1
fi

echo "🎉 Deployment completed successfully!"#!/bin/bash

set -e

echo "🚀 Deploying TaskFlow..."

echo "📥 Pulling latest code..."
git pull origin main

echo "🐳 Rebuilding and starting containers..."
docker compose up -d --build

echo "🩺 Checking application health..."
sleep 5

if curl -fs http://localhost/health > /dev/null; then
    echo "✅ TaskFlow is healthy!"
else
    echo "❌ Health check failed!"
    exit 1
fi

echo "🎉 Deployment completed successfully!"

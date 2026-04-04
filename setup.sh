#!/bin/bash
# Setup script for local development

echo "🚀 DateGen Setup"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

echo "✅ Docker found"
echo "✅ Docker Compose found"
echo ""

# Setup environment
echo "Setting up environment..."
if [ ! -f .env ]; then
    cp .env.template .env
    echo "✅ Created .env from template"
    echo "⚠️  Please edit .env with your API keys before starting!"
else
    echo "✅ .env already exists"
fi

echo ""

# Start services
echo "Starting Docker services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Access the app:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 To stop: docker-compose down"
echo "📊 To view logs: docker-compose logs -f"

#!/bin/bash
echo "Starting Qdrant..."
docker start itinerary_qdrant

echo "Starting Postgres..."
sudo service postgresql start

echo "Activating venv..."
source venv/bin/activate

echo "Starting API server on port 8001..."
uvicorn api:app --reload --host 0.0.0.0 --port 8001

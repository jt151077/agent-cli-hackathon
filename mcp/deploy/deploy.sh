#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

# Load mcp/.env file
if [ -f mcp/.env ]; then
  export $(grep -v '^#' mcp/.env | xargs)
fi

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"jeremy-k3c0v5rg"}
LOCATION=${GOOGLE_CLOUD_LOCATION:-"us-central1"}
SERVICE_NAME="weather-agent"
# Use Artifact Registry path
IMAGE_NAME="${LOCATION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}"

if [ -z "$PROJECT_ID" ] || [ -z "$LOCATION" ]; then
  echo "Error: PROJECT_ID and LOCATION must be set or available in environment"
  exit 1
fi

echo "Deploying ${SERVICE_NAME} to Cloud Run in project ${PROJECT_ID}, location ${LOCATION}..."

# Step 1: Build the container image using Cloud Build
# We run it from mcp/app directory to keep the context clean
echo "Building container image ${IMAGE_NAME}..."
gcloud builds submit mcp/app --tag "${IMAGE_NAME}" --project "${PROJECT_ID}"

# Step 2: Deploy to Cloud Run
echo "Deploying service ${SERVICE_NAME}..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --project "${PROJECT_ID}" \
  --region "${LOCATION}" \
  --port 8080 \
  --allow-unauthenticated \
  --set-secrets="WEATHER_API_KEY=weather-api-key:latest" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --quiet

# Step 3: Update mcp/.env with the URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --project "${PROJECT_ID}" --region "${LOCATION}" --format 'value(status.url)')
echo "Deployment successful. Service URL: ${SERVICE_URL}"

# Update mcp/.env file
if [ -f mcp/.env ]; then
  if grep -q "WEATHER_AGENT_URL=" mcp/.env; then
    sed -i "s|WEATHER_AGENT_URL=.*|WEATHER_AGENT_URL=${SERVICE_URL}|" mcp/.env
  else
    echo "WEATHER_AGENT_URL=${SERVICE_URL}" >> mcp/.env
  fi
else
  echo "WEATHER_AGENT_URL=${SERVICE_URL}" > mcp/.env
  echo "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" >> mcp/.env
  echo "GOOGLE_CLOUD_LOCATION=${LOCATION}" >> mcp/.env
fi

echo "Updated mcp/.env with WEATHER_AGENT_URL=${SERVICE_URL}"

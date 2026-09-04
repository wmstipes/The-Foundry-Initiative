# SignalForge Milestone 005 — FastAPI Rolling Update to 0.3.0

Date: 2026-08-27

## Result

The FastAPI Restaurant API was updated from version 0.2.0 to 0.3.0 using a Kubernetes rolling update.

## Image

wmstipes/signalforge-restaurant-api:0.3.0

## Confirmed

- New Docker image was built for linux/arm64
- Image was pushed to Docker Hub
- Kubernetes Deployment was updated to use the 0.3.0 image
- Rollout completed successfully
- /version returned 0.3.0 after APP_VERSION environment variable was corrected
- /status endpoint was added and tested

## Lesson Learned

The Docker image version and Kubernetes runtime configuration are separate. The app image was updated to 0.3.0, but the Deployment environment variable still set APP_VERSION=0.2.0 until corrected.

## Kubernetes Concepts Practiced

- kubectl set image
- kubectl set env
- rollout status
- rollout history
- image tags
- runtime environment variables
- app version verification

## Restaurant Analogy

The restaurant chain received the new 0.3.0 kitchen package, but the sign on the front counter still said 0.2.0. Updating the environment variable changed the sign to match the new kitchen package.

## Next

- Practice rollback to 0.2.0 and forward again to 0.3.0
- Add ConfigMap-based settings
- Add a simple /analyze endpoint
- Begin turning the app into the AI troubleshooting service

# SignalForge Milestone 006 — Rollback and Roll-Forward Practice

Date: 2026-08-27

## Result

Practiced a controlled Kubernetes rollback and roll-forward for the FastAPI Restaurant API.

## Starting State

- Image: wmstipes/signalforge-restaurant-api:0.3.0
- APP_VERSION: 0.3.0

## Exercise

- Inspected Deployment rollout history
- Identified prior known-good revision
- Rolled back to the 0.2.0 revision
- Verified /version returned 0.2.0
- Rolled forward to 0.3.0
- Verified /version returned 0.3.0

## Lesson Learned

A rollback restores a previous Deployment pod template revision. Because image changes and environment variable changes can create separate revisions, it is safer to inspect rollout history and roll back to a specific revision instead of assuming the immediately previous revision is the desired one.

## Kubernetes Concepts Practiced

- rollout history
- rollout undo
- rollback by revision
- rollout status
- image updates
- environment variable updates
- functional version verification

## Restaurant Analogy

The restaurant chain practiced reverting to a previous kitchen package and then rolling forward again to the newer menu. The exercise showed that the kitchen package and the front-counter version sign both matter.

## Next

- Add ConfigMap-based environment settings
- Add a basic /analyze endpoint
- Prepare the service to become the AI troubleshooting API

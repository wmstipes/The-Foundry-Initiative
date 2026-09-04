# The Foundry Initiative

The Foundry Initiative is a personal engineering, learning, and portfolio-building project focused on rebuilding confidence through deliberate practice, useful systems, and visible progress.

This repository is a practical workspace for turning hands-on technical work into evidence of capability across:

* DevOps and platform engineering
* Kubernetes and cloud-native systems
* applied AI and machine learning experiments
* infrastructure automation and observability
* architecture notes and technical decision records
* structured learning plans and project milestones
* small, finishable projects that demonstrate growth over time

## Guiding principle

Progress does not need to be dramatic to be real.

The goal is to keep building, documenting, learning, and turning experience into evidence.

## Current focus

The active workstream is **SignalForge**, a Raspberry Pi Kubernetes lab designed to build practical experience with Kubernetes, containerized applications, infrastructure troubleshooting, and eventually AI-assisted operations.

SignalForge uses a restaurant analogy to make Kubernetes concepts easier to understand:

* a container image is a packaged kitchen
* a Pod is a running kitchen station
* a Deployment is the manager keeping enough stations running
* a Service is the stable phone number
* a ConfigMap is the local settings sheet
* NodePort is the public front door
* the future AI agent is the operations manager

The current application is the **SignalForge Restaurant API**, a FastAPI service deployed to the Kubernetes cluster.

## SignalForge Restaurant API

The SignalForge Restaurant API is the first Kubernetes-hosted application in this project.

It currently includes:

* FastAPI application
* Docker image built for `linux/arm64`
* Kubernetes Deployment
* Kubernetes Service
* ConfigMap-driven runtime settings
* health and readiness endpoints
* version, menu, and status endpoints
* rules-based `POST /analyze` troubleshooting endpoint
* NodePort access for laptop-based testing
* FastAPI Swagger UI access through `/docs`
* Prometheus-format application metrics through `/metrics`
* lightweight in-cluster Prometheus manifests with Pod-level discovery

The long-term goal is to evolve this service into **ForgeOps**, an AI-assisted Kubernetes incident copilot that can help analyze cluster symptoms, summarize likely causes, and recommend next troubleshooting steps.

## Repository map

```text
The-Foundry-Initiative/
  apps/
    restaurant-api/        FastAPI application source, Dockerfile, and tests

  k8s/
    fastapi-restaurant/    Kubernetes manifests for the Restaurant API
    prometheus/            Lightweight Prometheus manifests and scrape configuration

  docs/
    milestones/            Project milestones and implementation notes
    architecture/          Architecture notes and technical decisions
    learning/              Learning plans, reflections, and study notes

  src/                      Shared or earlier implementation code
  tests/                    Shared or earlier automated tests
  experiments/              Prototypes and exploratory work

  ROADMAP.md                Project goals and future phases
  CONTRIBUTING.md           Working conventions for the project
```

## Current project status

The project has moved beyond the initial repository foundation phase and is now focused on the SignalForge Kubernetes learning lab.

Completed SignalForge milestones include:

* Raspberry Pi Kubernetes cluster online
* validation workload deployed successfully
* FastAPI Restaurant API deployed to Kubernetes
* Docker image built and deployed from Docker Hub
* rolling update performed
* rollback and roll-forward practiced
* runtime configuration moved into a ConfigMap
* first structured `/analyze` endpoint added
* NodePort access and external API testing confirmed
* Restaurant API testing and GitHub Actions CI added
* automated ARM64 Docker image publishing added
* versioned release `0.6.0` deployed
* Kubernetes manifests and validation stored in Git
* laptop-based `kubectl`, deployment, smoke-test, and operator helpers added
* operator runbook added
* Prometheus-format application metrics added at `/metrics`
* lightweight metrics-collection architecture selected

## Earlier utility: foundry-check

`foundry-check` is an earlier Python command-line utility in this repository.

It evaluates whether a local repository has a reasonable project foundation. It uses only the Python standard library at runtime and does not read secret contents.

The tool checks for baseline project structure, required documentation files, implementation and test directories, and suspicious tracked secret filenames.

It remains part of The Foundry Initiative as a small supporting utility and early proof of practice.

## SignalForge development workflow

The current development workflow is:

1. Develop the FastAPI application locally.
2. Build and push a `linux/arm64` Docker image.
3. Deploy the image to the Raspberry Pi Kubernetes cluster.
4. Validate the application through Kubernetes Services.
5. Capture each meaningful step as a milestone.
6. Gradually add automation, testing, observability, and AI-assisted troubleshooting.

Planned next steps include:

* deploy and validate the lightweight Prometheus collector
* confirm automatic target rediscovery when an application Pod is replaced
* add persistent NVMe-backed metrics storage when the cluster storage design is ready
* add Grafana and alerting only after the first collection layer is understood
* add Ingress as a cleaner external access pattern
* evaluate Loki and OpenTelemetry as later observability layers
* replace the rules-based `/analyze` logic with an AI-assisted troubleshooting workflow

## Why this project exists

The Foundry Initiative is not just a code repository.

It is a structured way to rebuild momentum, sharpen technical skills, and create visible proof of engineering growth through practical systems.

The purpose is to build useful artifacts, document the process, and turn learning into a portfolio of working evidence.

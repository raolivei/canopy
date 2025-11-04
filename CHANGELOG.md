# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-03-18

### Added

- Initial FastAPI backend scaffold with configuration, Celery worker stub, domain models, and pytest smoke test.
- Next.js + Tailwind frontend baseline with static export pipeline and placeholder dashboard UI.
- Dockerfiles for backend API and exported frontend.
- Kubernetes manifests (namespace, deployments, services, ingress, secrets example) plus aggregated `ledgerlight.yaml`.
- GitHub Actions workflow for building GHCR images and applying manifests on a self-hosted runner.
- Repository-wide `.gitignore`, documentation refresh, and project changelog.


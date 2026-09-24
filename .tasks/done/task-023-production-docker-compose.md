# Task 023: Add production Docker Compose configuration

## Story
As an operator, I want a production Docker Compose configuration for the AI Research dashboard so that the application can be built, started, restarted, and connected to the existing reverse-proxy network with predictable production settings.

## Product requirement
Add a root-level `docker-compose.yml` that defines the production application service using the repository's Docker image/build contract. The service must load production environment variables from `.env.production`, expose the dashboard on port `8000`, restart automatically unless explicitly stopped, and connect to both an application-private network and the existing external `proxy-tier` network used by other services on the same domain.

The Compose file must reflect this project's actual runtime. It must not copy unrelated Django-specific settings, migration commands, static-file volumes, or media volumes from the sister project unless the repository contains a matching application requirement.

## Acceptance Criteria
1. Compose file and service
   - A root-level `docker-compose.yml` exists and parses successfully with the installed Docker Compose implementation.
   - The file defines one production application service with a stable, project-appropriate service and container name.
   - The service builds from the repository root using the repository's production `Dockerfile`.
   - The service is configured with `restart: unless-stopped`.

2. Environment configuration
   - The service loads production configuration from `.env.production`.
   - Secrets and provider credentials are not hard-coded in the Compose file.
   - Any explicitly declared environment overrides are limited to settings required by this application and are documented.
   - The Compose configuration does not introduce the sister project's `RUN_MIGRATIONS` setting unless this project actually implements migrations.

3. Networking and exposure
   - The application listens on container port `8000`, matching the dashboard's production runtime.
   - The host-facing production port is `8003`, published as `8003:8000` unless the reverse-proxy design intentionally omits direct host publishing and documents the equivalent routing.
   - The service joins a private application network for project-local connectivity.
   - The service joins the external `proxy-tier` network using the exact network name expected by the shared reverse proxy.
   - The external network is declared as external so Compose does not attempt to manage or recreate it.
   - Host port publishing is evaluated against the deployment's reverse-proxy design; when direct publishing is used, it must bind host port `8003` to container port `8000`.

4. Volumes and persistence
   - No static-file or media volumes are added unless the dashboard's containerized runtime writes data that must persist across replacement.
   - Any required persistent volume is named explicitly and mounted only at an application path supported by the code.
   - Report and session-knowledge retention behavior is documented, including whether those directories are intentionally ephemeral or persisted in production.

5. Production usability
   - The Compose configuration includes a clear startup command in the README, including the prerequisite creation of the external `proxy-tier` network when it does not exist.
   - The documented command uses the production environment file and does not expose secrets in shell history.
   - The dashboard's Ollama connectivity requirements and reverse-proxy assumptions are documented.
   - A health check or equivalent operational readiness check is added if it is supported by the application and image; otherwise the omission and operational check are documented.

6. Validation
   - `docker compose config` succeeds with a safe example environment file or documented placeholder variables.
   - The image builds successfully with `docker compose build` in an environment with Docker available.
   - The service starts successfully with `docker compose up -d` in a configured production-like environment, or the documented validation limitation is recorded when Docker/Ollama/proxy infrastructure is unavailable.
   - Existing Python tests, Black, and flake8 continue to pass.

## Non-Goals
- This task does not configure DNS, TLS certificates, or reverse-proxy routing rules outside the Compose network attachment required for integration.
- This task does not provision Ollama or package an Ollama server into the application Compose file.
- This task does not add application migrations, database services, Redis, Celery, or unrelated infrastructure.
- This task does not copy Django static/media volume behavior from the sister project without evidence that this dashboard needs it.

## Security and privacy notes
- Keep `.env.production` out of version control and provide only a sanitized example file when needed.
- Do not put API keys, Ollama credentials, or private network details directly in tracked Compose configuration.
- Avoid broad host-path mounts and privileged container settings.
- Use the smallest network and filesystem access required by the dashboard.

## UX and operations acceptance
- An operator can identify the service, port, networks, environment file, and persistence behavior by reading the Compose file and README.
- Deployment failure messages identify missing Docker, `.env.production`, image build prerequisites, or the external `proxy-tier` network without leaking secrets.
- Existing dashboard behavior remains unchanged when run through the documented production Compose workflow.

## Open decisions for technical review
- Confirm the production image contract and whether a `Dockerfile` already exists at the repository root.
- Decide whether direct host publishing on `8000` is required when the reverse proxy is attached to `proxy-tier`.
- Decide whether reports and any session data should persist across container replacement.
- Define the reverse-proxy service/network alias and routing labels or configuration, if this deployment expects them in Compose.
- Confirm the application health endpoint or an appropriate container-level readiness check.

## Ready for engineering
This ticket is ready for technical review after the open deployment decisions are resolved. Product-owner grooming is complete; implementation should begin only after approval or refinement of the acceptance criteria and deployment assumptions.

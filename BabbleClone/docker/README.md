Docker compose for local frontend + mock backend

This directory contains a `docker-compose.yml` at the repository root that starts the frontend (mounted from the repo) and a lightweight mock backend used for local testing.

Run the stack locally:

```bash
# from repository root
docker compose up --build
```

Behavior:
- Frontend is available at: http://localhost:5173
- Mock backend HTTP: http://localhost:3000
- Mock backend WebSocket: ws://localhost:3000/ws

Stop the stack:

```bash
docker compose down
```

Notes:
- The compose file mounts the `frontend` folder into the `frontend` container for fast local iteration.
- I did not modify any files under `backend/`; the mock backend lives under `docker/mock-backend`.

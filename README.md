# WAN Audit App

WAN Audit App is a full-stack monitoring dashboard for GNS3-based network topologies. It imports GNS3 projects into a MySQL-backed database, maps devices to sites or backbones, and exposes the data through a FastAPI backend and a React frontend.

## Overview

- Backend: FastAPI + SQLAlchemy
- Frontend: React + TypeScript + Vite
- Database: MySQL / MariaDB
- Network emulation: GNS3
- Auth: session-based admin login

## Project structure

- `backend/app/` — API, database models, routers, and services
- `src/` — frontend application
- `requirements.txt` — Python dependencies
- `package.json` — frontend scripts
- `.env.example` — environment template

## Prerequisites

Before running the app, make sure you have:

- Python 3.11+
- Node.js 18+
- MySQL or MariaDB running locally or on a reachable host
- A running GNS3 server reachable by the configured URL

## Environment setup

1. Copy the example environment file:

```bash
copy .env.example .env
```

2. Update the values in `.env` with your environment-specific settings.

Example values:

```env
SECRET_KEY=replace-with-a-long-random-secret
DB_HOST=localhost
DB_PORT=3306
DB_NAME=monitoring
DB_USER=root
DB_PASSWORD=your_mysql_password
GNS3_URL=http://127.0.0.1:3080
DEVICE_SSH_USERNAME=
DEVICE_SSH_PASSWORD=
```

Important notes:

- `SECRET_KEY` must be set or the backend will fail to start.
- `DB_*` values must match your database instance.
- `GNS3_URL` must point to the GNS3 API endpoint.

## Backend setup

From the project root:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Then start the API:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at:

- http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## Frontend setup

From the project root:

```bash
npm install
npm run dev
```

The frontend runs on:

- http://localhost:5173

## Database initialization

The application uses SQLAlchemy models and expects the target MySQL database to exist.

Typical workflow:

```bash
cd backend
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
```

If you maintain a custom admin user, create it with the project helper scripts if available.

## Authentication

The app exposes an admin session flow:

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

Use the admin credentials configured in the database to log in from the frontend.

## GNS3 integration

The GNS3 service imports projects, nodes, and links from the GNS3 API:

- `GET /gns3/projects`
- `GET /gns3/projects/{project_id}/nodes`
- `GET /gns3/projects/{project_id}/links`
- `POST /gns3/projects/{project_id}/import`

This import process:

- creates or updates devices from GNS3 nodes,
- associates devices with sites or backbones by matching names,
- imports interface ports,
- creates topology links between source and destination devices.

## Useful commands

Frontend build check:

```bash
npm run build
```

Frontend lint check:

```bash
npm run lint
```

Python syntax validation:

```bash
python -m compileall backend
```

## Notes

This project is intended for production-style network inventory and topology monitoring, but it still requires a clean database, valid credentials, and a reachable GNS3 instance before use.


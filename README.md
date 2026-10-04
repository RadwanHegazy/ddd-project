# DDD E-Commerce Practice Project

## Overview

This repository is an educational practice project for learning and applying ideas from Domain-Driven Design (DDD) and layered architecture. It is not a real e-commerce product and is not intended for production use.

The example is a small e-commerce API built with FastAPI. It includes users and authentication, products, order creation and checkout, payment webhooks, notifications, PostgreSQL persistence, Redis-backed caching and rate limiting, and automated tests.

The architecture and study approach are inspired by the book *Architecture Patterns with Python*, also known as *Cosmic Python*:

- Book introduction: https://www.cosmicpython.com/book/introduction

## Architecture

The code is organized around business behavior and separates it from web, database, and external-service details:

- **Domain (`domain/`)**: Business entities and rules. `Product` controls stock allocation, `Order` controls its items and status transitions, and domain exceptions represent invalid business operations.
- **Service layer (`service_layer/`)**: Application use cases such as creating products and orders, handling successful payments, and sending notifications. These services coordinate domain objects and persistence without depending directly on FastAPI routes.
- **Repositories and Unit of Work (`adapters/repository.py`, `service_layer/unit_of_work.py`)**: Repository abstractions provide access to products, orders, and users. The Unit of Work groups repository operations into a transaction and commits or rolls back changes. Both SQLAlchemy-backed and in-memory fake implementations are provided.
- **Adapters (`adapters/`)**: Implementations for infrastructure and external systems, including SQLAlchemy persistence, password hashing, JWTs, Redis, payment gateways, notifications, and shipping.
- **Entrypoints (`entrypoints/`)**: The FastAPI application, versioned HTTP routes, request/response schemas, dependency wiring, and rate limiting. Routes translate HTTP requests into calls to the service layer.

A typical request follows this path:

```text
HTTP request
	-> FastAPI route and schema
	-> service-layer use case
	-> Unit of Work and repository
	-> domain behavior
	-> commit transaction
	-> HTTP response
```

This is a learning implementation of these patterns, not a claim that every part of the codebase follows strict DDD rules.

## Run With Docker

Docker Compose starts the API, PostgreSQL, and Redis. The FastAPI source directory is mounted into the container, and Uvicorn reloads the server when Python files change.

From the project root, build and start the services in the background:

```bash
docker compose up --build -d
```

The API is available at <http://localhost:8000>. Interactive API documentation is at <http://localhost:8000/docs>.

To view logs or stop the services:

```bash
docker compose logs -f fastapi
docker compose down
```

The API uses PostgreSQL on port `5432` and Redis on port `6379`. The separate test PostgreSQL service uses port `5433` and is started only when requested below.

## Run Tests

The suite includes unit tests using in-memory fakes and database integration tests using the `test_postgres` Compose service. Run pytest on your host machine so the integration tests can connect to the published database port.

Create and activate a Python virtual environment, then install the project dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Start the test database:

```bash
docker compose up -d test_postgres
```

Wait until PostgreSQL reports that it is ready to accept connections, then run the complete test suite from the project root:

```bash
pytest -q
```

The integration tests connect to `localhost:5433/test_db` using the development credentials configured in `docker-compose.yml`. They create and clear tables in that test database, so do not point the test configuration at any database containing data you need to keep.

## Project Layout

```text
adapters/       Database and external-service implementations
domain/         Business entities, rules, and exceptions
entrypoints/    FastAPI application, routes, and schemas
service_layer/  Use cases, handlers, and Unit of Work
tests/          Unit and PostgreSQL integration tests
```

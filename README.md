# FastAPI Users Application

This is a FastAPI application for managing users with authentication and authorization features. The application supports user registration, login, and role-based access control with a MySQL database and Redis for token blacklisting.

## Features

- User registration
- User login and logout
- JWT-based authentication
- Role-based access control
- Admin-only endpoints
- Database initialization with a predefined admin user

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository:
    ```bash
    https://github.com/HosseineShams/fastapi-users
    cd fastapi-users
    ```

2. Create a `.env` file in the root directory with the following content:
    ```env
    DATABASE_URL=mysql+pymysql://yourusername:yourpassword@db/fastapi_users_db
    SECRET_KEY=your_secret_key
    REDIS_URL=redis://redis:6379/1
    ADMIN_USERNAME=admin
    ADMIN_EMAIL=admin@example.com
    ADMIN_PASSWORD=adminpassword
    ```

3. Build and start the Docker containers:
    ```bash
    docker-compose up --build
    ```

4. Initialize the database with the predefined admin user:
    ```bash
    docker ps
    ```

    Find the container ID of the web service, then run:
    ```bash
    docker exec -it <container_id> python -m app.init_db
    ```

### API Endpoints

#### User Management

- **Create User**: `POST /api/users`
- **Login**: `POST /api/login`
- **Logout**: `POST /api/logout`
- **Get All Users**: `GET /api/users` (Admin only)
- **Get User by ID**: `GET /api/users/{user_id}`
- **Update User**: `PUT /api/users/{user_id}`
- **Delete User**: `DELETE /api/users/{user_id}`

#### Permission Management

- **Create Permission**: `POST /api/permissions` (Admin only)
- **Get Permissions for Role**: `GET /api/permissions/{role}` (Admin only)

#### Admin Only

- **Admin Only Endpoint**: `GET /api/admin`
- **Make User Admin**: `POST /api/users/{user_id}/make_admin` (Admin only)

### Postman Documentation

For detailed API documentation and testing, please refer to the [Postman documentation](https://documenter.getpostman.com/view/25778869/2sA3rwNaUf).

### Running the Application

After starting the Docker containers and initializing the database, the FastAPI application will be accessible at `http://127.0.0.1:8000`.


# Routine Grid

A habit tracking application that allows users to track both singular (yes/no completion) and timed habits (duration-based) in a structured format.

Built using UV, Django, and PostgreSQL.

## Overview

Routine Grid helps users build consistent routines by tracking daily habits. The application supports two habit types:

- **Singular** habits (completed or not - e.g., "Did you meditate today?")
- **Timed** habits (tracked with duration values - e.g., "45 minutes of exercise")

## Features

- **User Management**

  - User registration and authentication with JWT
  - User profile management
  - Password reset functionality

- **Habit Tracking**

  - Create, view, update, and archive/unarchive habits
  - Mark habits as completed with date-specific entries
  - Add notes to habit entries
  - Track time-based habits with custom values
  - Filter habits by active/archived status
  - Filter entries by date range and habits

- **API Documentation**
  - Interactive API documentation with Scalar

## Technology Stack

- **Backend**
  - Python 3.13
  - Django 5.2
  - Django REST Framework
  - PostgreSQL
  - JWT Authentication
  - drf-spectacular (Swagger/OpenAPI)

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd routine-grid
   ```

2. **Set up a virtual environment using UV**

   ```bash
   uv venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   uv sync
   ```

4. **Create environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and settings
   ```

5. **Run migrations**

   ```bash
   uv run manage.py migrate
   ```

6. **Create a superuser**

   ```bash
   uv run manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   uv run manage.py runserver
   ```

## Environment Variables

The following environment variables can be configured in the `.env` file:

- `DATABASE_URL`: PostgreSQL database connection string
- `SECRET_KEY`: Django secret key for security
- `DEBUG`: Set to True for development, False in production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CORS_ALLOWED_ORIGINS_ENV`: Comma-separated list of allowed CORS origins

## API Endpoints

### Authentication

- `POST /api/v1/auth/register/`: Register a new user
- `POST /api/v1/auth/login/`: Obtain JWT tokens
- `POST /api/v1/auth/refresh/`: Refresh JWT token
- `POST /api/v1/auth/password_reset/`: Initiate password reset

### User Management

- `GET /api/v1/users/me/`: Get current user profile
- `PUT/PATCH /api/v1/users/me/`: Update user profile
- `DELETE /api/v1/users/me/`: Delete user account

### Habits

- `GET /api/v1/habits/`: List user's habits (with optional archive filter)
- `POST /api/v1/habits/`: Create a new habit
- `GET /api/v1/habits/{id}/`: Get a specific habit
- `PUT /api/v1/habits/{id}/`: Update a habit (full)
- `PATCH /api/v1/habits/{id}/`: Update a habit (partial)
- `DELETE /api/v1/habits/{id}/`: Delete a habit (hard delete)
- `POST /api/v1/habits/{id}/archive/`: Archive a habit (soft delete)
- `POST /api/v1/habits/{id}/unarchive/`: Unarchive a habit

### Habit Entries

- `GET /api/v1/entries/`: List habit entries (with filters)
- `POST /api/v1/entries/`: Create a new habit entry
- `GET /api/v1/entries/{id}/`: Get a specific habit entry
- `PUT/PATCH /api/v1/entries/{id}/`: Update an entry
- `DELETE /api/v1/entries/{id}/`: Delete an entry

### API Documentation

- `/api/schema.yaml`: OpenAPI schema
- `/`: Scalar API documentation

## Testing

The project includes comprehensive tests for API endpoints:

```bash
uv run manage.py test
```

## Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new features
- Document API endpoints
- Use Django's model validation

## Contact

Heet Patel - heetkpatel30@gmail.com

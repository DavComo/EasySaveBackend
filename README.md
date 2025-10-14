# EasySave Backend API

## Overview

EasySave Backend is a FastAPI-based REST API service that provides user management and hierarchical data storage functionality. The system uses PostgreSQL for data persistence and implements secure authentication using access keys and password hashing.

## Architecture

### Core Components

1. **FastAPI Server** (`server.py`)
   - RESTful API endpoints for user and block management
   - Middleware for authentication and CORS
   - Custom OpenAPI schema generation

2. **Database Service** (`dbService.py`)
   - PostgreSQL database interaction layer
   - Transaction management with automatic rollback
   - User and block CRUD operations

3. **Data Models**
   - `User` - User account management with environment support
   - `Block` - Hierarchical data storage units
   - `api_schemas.py` - Pydantic models for API request/response validation

4. **Utilities** (`utils.py`)
   - Unique ID generation with environment prefixes
   - Password hashing using Argon2
   - Email validation
   - Access key generation

5. **Custom Exceptions** (`customExceptions.py`)
   - Domain-specific exceptions for better error handling

## Key Features

### User Management
- User registration with email validation
- Secure password hashing (Argon2)
- Access key-based authentication
- Support for production and test environments
- User profile updates

### Data Storage (Blocks)
- Hierarchical identifier system (env.username.path.to.data)
- CRUD operations on data blocks
- User-scoped data isolation
- Pattern-based data retrieval

### Security
- Middleware-based authentication for protected endpoints
- Access key verification (128-character hexadecimal)
- Secure password hashing
- CORS support with configurable origins

## Environment System

The system supports two environments:
- **prod** - Production environment
- **test** - Testing environment

Each user is assigned to an environment, and their unique ID is prefixed with the environment name (e.g., `prod.johndoe`).

## API Endpoints

### Public Endpoints
- `POST /create_user` - Register a new user
- `GET /login` - Authenticate and receive access key

### Protected Endpoints (require authentication headers)
- `GET /get_user` - Retrieve user information
- `PATCH /update_user` - Update user profile
- `POST /create_block` - Create a new data block
- `GET /get_blocks` - Retrieve data blocks
- `PATCH /update_block` - Update a data block
- `POST /delete_block` - Delete a data block

### Authentication
Protected endpoints require two headers:
- `RequesterUsername` - Username of the authenticated user
- `RequesterAccessKey` - 128-character access key

## Database Schema

### Users Table
- `username` - Unique username
- `uniqueid` - Environment-prefixed unique identifier (e.g., prod.johndoe)
- `email` - User email address
- `accessKey` - Authentication access key
- `password` - Argon2 hashed password

### Data Table
- `identifier` - Hierarchical identifier (env.username.path)
- `value` - Data content (string)

## Unique Identifier System

The system uses a dot-separated hierarchical identifier system:

Format: `{environment}.{username}[.{subfolder1}[.{subfolder2}...]]`

Examples:
- `prod.johndoe` - User's root
- `prod.johndoe.documents` - User's documents folder
- `prod.johndoe.documents.work.report1` - Nested structure

This allows for:
- Namespace isolation per user
- Hierarchical organization of data
- Pattern-based queries (e.g., retrieve all items under `prod.johndoe.documents.*`)

## Setup and Configuration

### Environment Variables
- `DATABASE_DSN` - PostgreSQL connection string

### Dependencies
- FastAPI - Web framework
- psycopg2 - PostgreSQL adapter
- argon2-cffi - Password hashing
- pydantic - Data validation

## Error Handling

The system implements comprehensive error handling:
- `NonuniqueUsername` - Raised when attempting to create duplicate usernames
- `InvalidEmail` - Raised for invalid email formats
- HTTP 401 - Authentication failures
- HTTP 422 - Validation errors
- HTTP 500 - Server errors

## Development and Maintenance

### Code Organization
- Each module has a single, well-defined responsibility
- Database operations are centralized in `DBService`
- API schemas are separated from business logic
- Utility functions are pure and reusable

### Testing
The system supports a test environment (`envs.test`) for safe testing without affecting production data.

### Adding New Endpoints
1. Define request/response schemas in `api_schemas.py`
2. Add endpoint handler in `server.py`
3. Implement business logic in `DBService` if needed
4. Update `custom_openapi()` to include new schemas

### Adding New Features
1. Update data models if needed (`User`, `Block`)
2. Add utility functions if needed (`utils.py`)
3. Implement database operations in `DBService`
4. Create API endpoints in `server.py`
5. Add appropriate validation and error handling

## Security Considerations

1. **Password Security**
   - Passwords are hashed using Argon2 before storage
   - Never stored or transmitted in plain text

2. **Access Keys**
   - Generated using cryptographically secure random number generator
   - 128 characters (64 bytes) for strong security

3. **Authentication**
   - All protected endpoints verify access keys
   - Invalid credentials return 401 status

4. **SQL Injection Prevention**
   - All database queries use parameterized statements
   - User input is never directly interpolated into SQL

5. **CORS**
   - Configurable allowed origins
   - Currently allows all origins (consider restricting in production)

## API Documentation

Interactive API documentation is available at `/docs` when the server is running.

The API uses OpenAPI/Swagger specification for complete documentation of all endpoints, request/response models, and validation rules.

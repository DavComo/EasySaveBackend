# EasySave Backend Maintenance Guide

This guide provides comprehensive information for developers and maintainers of the EasySave Backend API system.

## Table of Contents
1. [Code Structure](#code-structure)
2. [Module Dependencies](#module-dependencies)
3. [Database Schema](#database-schema)
4. [Adding New Features](#adding-new-features)
5. [Common Maintenance Tasks](#common-maintenance-tasks)
6. [Troubleshooting](#troubleshooting)
7. [Testing Guidelines](#testing-guidelines)
8. [Deployment](#deployment)

---

## Code Structure

### Module Overview

```
EasySaveBackend/
├── server.py              # FastAPI application and endpoint definitions
├── dbService.py          # Database interaction layer
├── user.py               # User data model
├── block.py              # Block data model
├── api_schemas.py        # Pydantic request/response models
├── utils.py              # Utility functions (hashing, validation, ID generation)
├── customExceptions.py   # Domain-specific exception classes
├── README.md             # Project overview and architecture
├── API_DOCUMENTATION.md  # Complete API reference
└── MAINTENANCE.md        # This file
```

### Module Responsibilities

**server.py**
- FastAPI application initialization
- HTTP endpoint definitions
- Middleware configuration (CORS, authentication)
- Request/response handling
- Error handling and status codes

**dbService.py**
- PostgreSQL connection management
- Database CRUD operations
- Transaction handling with automatic rollback
- SQL query execution
- Data validation at database layer

**user.py**
- User account data model
- User attribute getters/setters
- Automatic unique ID generation
- Password hashing integration

**block.py**
- Block data model for hierarchical storage
- Block serialization/deserialization
- Factory methods for database results

**api_schemas.py**
- Pydantic models for request validation
- Response schema definitions
- OpenAPI documentation integration
- Type safety for API contracts

**utils.py**
- Unique ID generation and parsing
- Password hashing (Argon2)
- Email validation
- Access key generation
- Environment enum definition

**customExceptions.py**
- NonuniqueUsername exception
- InvalidEmail exception
- Domain-specific error handling

---

## Module Dependencies

### Dependency Graph
```
server.py
  ├── api_schemas.py
  ├── dbService.py
  │   ├── user.py
  │   │   └── utils.py
  │   ├── block.py
  │   ├── utils.py
  │   └── customExceptions.py
  └── customExceptions.py
```

### External Dependencies
- **FastAPI**: Web framework
- **psycopg2**: PostgreSQL database adapter
- **argon2-cffi**: Password hashing
- **pydantic**: Data validation and serialization
- **uvicorn**: ASGI server (for running the application)

### Installing Dependencies
```bash
pip install fastapi psycopg2-binary argon2-cffi pydantic uvicorn
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    username VARCHAR(255) PRIMARY KEY,
    uniqueid VARCHAR(512) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    accessKey CHAR(128) UNIQUE NOT NULL,
    password TEXT NOT NULL
);
```

**Columns:**
- `username`: Unique username for login
- `uniqueid`: Environment-prefixed identifier (e.g., "prod.johndoe")
- `email`: User's email address
- `accessKey`: 128-character hex authentication token
- `password`: Argon2 hashed password

### Data Table
```sql
CREATE TABLE data (
    identifier VARCHAR(1024) PRIMARY KEY,
    value TEXT
);
```

**Columns:**
- `identifier`: Full hierarchical path (e.g., "prod.johndoe.documents.report1")
- `value`: The data content (string)

### Setting Up Database
1. Install PostgreSQL
2. Create a database
3. Run schema creation SQL
4. Set `DATABASE_DSN` environment variable:
   ```
   DATABASE_DSN="postgresql://user:password@localhost:5432/dbname"
   ```

---

## Adding New Features

### Adding a New API Endpoint

1. **Define Request/Response Schemas** (api_schemas.py)
   ```python
   class NewFeatureRequest(BaseModel):
       param1: str = Field(description="...")
       param2: int = Field(description="...")
   
   class NewFeatureResponse(BaseModel):
       result: str = Field(description="...")
   ```

2. **Add Database Method** (dbService.py)
   ```python
   def newFeatureOperation(self, param1: str, param2: int):
       """
       Description of what this does.
       
       Args:
           param1: Description
           param2: Description
       
       Returns:
           Description of return value
       """
       # Implementation
       self.modify_data("SQL HERE", [param1, str(param2)])
   ```

3. **Create API Endpoint** (server.py)
   ```python
   @app.post("/new_feature", response_model=NewFeatureResponse)
   async def new_feature(request: Request, 
                        userRequest: Annotated[NewFeatureRequest, Query()]):
       """
       Endpoint description.
       
       Args:
           request: HTTP request with auth headers
           userRequest: Request parameters
       
       Returns:
           NewFeatureResponse with result
       """
       # Implementation
       result = dbServiceInstance.newFeatureOperation(
           userRequest.param1, 
           userRequest.param2
       )
       return {"result": result}
   ```

4. **Update OpenAPI Schema** (server.py, custom_openapi function)
   ```python
   schema["components"]["schemas"]["NewFeatureRequest"] = \
       NewFeatureRequest.model_json_schema()
   schema["components"]["schemas"]["NewFeatureResponse"] = \
       NewFeatureResponse.model_json_schema()
   ```

5. **Update Documentation**
   - Add endpoint to API_DOCUMENTATION.md
   - Update README.md if architecture changes

### Adding a New Data Model

1. **Create Model Class** (e.g., newmodel.py)
   ```python
   """
   Module description.
   """
   
   class NewModel:
       """
       Class description.
       """
       def __init__(self, ...):
           """Initialize description."""
           # Implementation
   ```

2. **Add Database Methods** (dbService.py)
   - Create methods for CRUD operations
   - Follow existing patterns (modify_data, query_dict_data)

3. **Import in Server** (server.py)
   ```python
   from newmodel import NewModel
   ```

### Adding Utility Functions

1. **Add to utils.py**
   ```python
   def newUtilityFunction(param: str) -> str:
       """
       Function description.
       
       Args:
           param: Parameter description
       
       Returns:
           Return value description
       
       Example:
           result = newUtilityFunction("test")
       """
       # Implementation
   ```

2. **Write Tests** (if test framework exists)

---

## Common Maintenance Tasks

### Updating Password Hashing
If changing password hashing algorithm:
1. Update `utils.hashPassword()` and `utils.verifyHash()`
2. Consider migration strategy for existing passwords
3. Update documentation

### Adding Database Indexes
For performance optimization:
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_data_identifier ON data(identifier);
```

### Rotating Access Keys
All users:
```python
# In dbService.py, add method:
def rotateAllAccessKeys(self):
    users = self.query_dict_data("SELECT username FROM users", [])
    for user in users:
        new_key = utils.generateAccessKey()
        self.modify_data(
            "UPDATE users SET accessKey = %s WHERE username = %s",
            [new_key, user['username']]
        )
```

### Adding Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In functions:
logger.info(f"User {username} logged in")
logger.error(f"Failed to create user: {e}")
```

### Environment Variable Management
Create `.env` file (add to .gitignore):
```
DATABASE_DSN=postgresql://user:pass@localhost:5432/dbname
LOG_LEVEL=INFO
```

Load in code:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Troubleshooting

### Common Issues

**Issue: "Authorization credentials required"**
- **Cause**: Missing or incorrect authentication headers
- **Solution**: Ensure `RequesterUsername` and `RequesterAccessKey` headers are set
- **Check**: Verify access key is exactly 128 characters

**Issue: "Invalid Unique ID"**
- **Cause**: Malformed unique identifier
- **Solution**: Ensure format is `{env}.{username}[.{path}...]`
- **Check**: Environment must be "prod" or "test"

**Issue: Connection to database failed**
- **Cause**: Invalid DATABASE_DSN or database not running
- **Solution**: Check environment variable and PostgreSQL status
- **Check**: `psql -d $DATABASE_DSN` to test connection

**Issue: Password verification always fails**
- **Cause**: Password hashing/verification mismatch
- **Solution**: Ensure consistent Argon2 configuration
- **Check**: Test with `utils.verifyHash()` directly

**Issue: CORS errors in browser**
- **Cause**: Request from unauthorized origin
- **Solution**: Add origin to `origins` list in server.py
- **Check**: Current config allows all origins (`allow_origins=["*"]`)

### Debug Mode

Enable detailed error messages:
```python
# In server.py
app = FastAPI(root_path="/api", debug=True)
```

### Database Connection Debugging
```python
# Test connection
import psycopg2
import os

dsn = os.getenv("DATABASE_DSN")
try:
    conn = psycopg2.connect(dsn)
    print("Connection successful")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
```

---

## Testing Guidelines

### Manual Testing

**Test User Creation:**
```bash
curl -X POST "http://localhost:8000/api/create_user?username=testuser&email=test@example.com&password=testpass"
```

**Test Login:**
```bash
curl "http://localhost:8000/api/login?username=testuser&password=testpass"
```

**Test Protected Endpoint:**
```bash
curl -H "RequesterUsername: testuser" \
     -H "RequesterAccessKey: [key from login]" \
     "http://localhost:8000/api/get_user?username=testuser"
```

### Unit Testing Framework
If adding unit tests, consider:
- **pytest** for Python testing
- **pytest-asyncio** for async endpoint testing
- **unittest.mock** for database mocking

Example test structure:
```python
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_create_user():
    response = client.post("/create_user?username=test&email=test@test.com&password=pass")
    assert response.status_code == 204
```

### Integration Testing
Test complete workflows:
1. Create user
2. Login
3. Create block
4. Retrieve blocks
5. Update block
6. Delete block
7. Cleanup

---

## Deployment

### Production Checklist

- [ ] Set `DATABASE_DSN` environment variable
- [ ] Configure CORS origins (restrict from `["*"]`)
- [ ] Set up HTTPS/TLS
- [ ] Configure reverse proxy (nginx/Apache)
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Set up database backups
- [ ] Document deployment configuration

### Running with Uvicorn

**Development:**
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

**Production:**
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn (Production)
```bash
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t easysave-backend .
docker run -p 8000:8000 -e DATABASE_DSN="..." easysave-backend
```

### Environment-Specific Configuration

**Development:**
- `debug=True`
- Verbose logging
- Allow all CORS origins

**Production:**
- `debug=False`
- Error logging only
- Restricted CORS origins
- HTTPS required
- Rate limiting enabled

---

## Code Style and Standards

### Docstring Format
Follow Google-style docstrings:
```python
def function_name(param1: str, param2: int) -> bool:
    """
    Short description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ExceptionType: When this exception is raised
    
    Example:
        result = function_name("test", 42)
    """
```

### Type Hints
Always use type hints:
```python
def get_user(username: str) -> Optional[User]:
    ...
```

### Error Handling
- Use specific exception types
- Provide helpful error messages
- Log errors appropriately
- Return appropriate HTTP status codes

### SQL Queries
- Always use parameterized queries
- Never interpolate user input directly
- Use the `modify_data` and `query_data` wrappers

---

## Security Considerations

### Password Security
- Never log passwords
- Always hash before storage
- Use Argon2 with current settings
- Don't send passwords in responses

### Access Key Security
- Generate with cryptographically secure random
- 128 characters minimum
- Store securely
- Rotate periodically

### SQL Injection Prevention
- Use parameterized queries
- Validate input types
- Sanitize user input

### Input Validation
- Validate email formats
- Check identifier formats
- Verify data types
- Limit string lengths

---

## Performance Optimization

### Database
- Add indexes on frequently queried columns
- Use connection pooling
- Optimize query patterns
- Consider caching for read-heavy operations

### API
- Implement pagination for list endpoints
- Add rate limiting
- Cache static responses
- Use async operations

---

## Contact and Support

For questions or issues:
1. Check this maintenance guide
2. Review code comments and docstrings
3. Check API documentation
4. Contact the development team

Last Updated: October 2025

# EasySave API Documentation

## Base URL
All API endpoints are accessible at: `/api`

## Authentication

### Public Endpoints (No Authentication Required)
- `POST /create_user`
- `GET /login`

### Protected Endpoints (Authentication Required)
All other endpoints require authentication via HTTP headers:
- `RequesterUsername`: Your username
- `RequesterAccessKey`: Your 128-character access key (obtained from `/login`)

**Example:**
```bash
curl -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: a3f5d2e8..." \
     https://api.example.com/api/get_user?username=johndoe
```

---

## User Management Endpoints

### Create User
**Endpoint:** `POST /create_user`  
**Authentication:** None (Public)  
**Description:** Register a new user account.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Desired username (must be unique) |
| email | string | Yes | Email address (must be valid format) |
| password | string | Yes | Plain-text password (will be hashed) |
| test | boolean | No | Whether this is a test user (default: false) |

**Response Codes:**
- `204 No Content`: User created successfully
- `409 Conflict`: Username already exists
- `422 Unprocessable Entity`: Invalid email format

**Example:**
```bash
curl -X POST "https://api.example.com/api/create_user?username=johndoe&email=john@example.com&password=securepass123"
```

---

### Get User
**Endpoint:** `GET /get_user`  
**Authentication:** Required  
**Description:** Retrieve user profile information. At least one search parameter must be provided.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | No* | Search by username |
| uniqueid | string | No* | Search by unique ID (e.g., prod.johndoe) |
| email | string | No* | Search by email address |
| accessKey | string | No* | Search by access key |

*At least one parameter must be provided.

**Response:**
```json
{
  "env": "prod",
  "username": "johndoe",
  "uniqueid": "prod.johndoe",
  "email": "john@example.com"
}
```

**Response Codes:**
- `200 OK`: User found
- `401 Unauthorized`: Invalid authentication credentials
- `500 Internal Server Error`: No search parameters provided

**Example:**
```bash
curl -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: a3f5d2e8..." \
     "https://api.example.com/api/get_user?username=johndoe"
```

---

### Update User
**Endpoint:** `PATCH /update_user`  
**Authentication:** Required  
**Description:** Update user profile fields. Only updates the authenticated user's own profile.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| newValuesJSON | string | Yes | JSON string with field:value pairs to update |

**Allowed Fields in JSON:**
- `email`: New email address (must be valid format)
- `accessKey`: New access key
- `password`: New password hash

**Example JSON:**
```json
{
  "email": "newemail@example.com",
  "password": "newhashhere"
}
```

**Response Codes:**
- `204 No Content`: User updated successfully
- `401 Unauthorized`: Invalid authentication credentials
- `422 Unprocessable Entity`: Invalid field name or email format

**Example:**
```bash
curl -X PATCH \
     -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: a3f5d2e8..." \
     "https://api.example.com/api/update_user?newValuesJSON=%7B%22email%22%3A%22new%40example.com%22%7D"
```

---

### Login
**Endpoint:** `GET /login`  
**Authentication:** None (Public)  
**Description:** Authenticate user and receive access key for subsequent API calls.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Username to authenticate |
| password | string | Yes | Plain-text password |

**Response:**
```json
{
  "accessKey": "a3f5d2e8...128 character hex string"
}
```

**Response Codes:**
- `200 OK`: Login successful, access key returned
- `401 Unauthorized`: Invalid username or password
- `500 Internal Server Error`: Database error

**Example:**
```bash
curl "https://api.example.com/api/login?username=johndoe&password=securepass123"
```

---

## Block Management Endpoints

Blocks are hierarchical data storage units. Each block has an identifier following the pattern:
`{environment}.{username}.{path}`

For example: `prod.johndoe.documents.report1`

### Create Block
**Endpoint:** `POST /create_block`  
**Authentication:** Required  
**Description:** Create a new data block under your user namespace.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| extendedIdentifier | string | Yes | Path after username (e.g., "documents.report1") |
| value | string | Yes | The data content to store (can be empty) |

**Full Identifier:** The system automatically prepends your environment and username to create the full identifier:
`{env}.{username}.{extendedIdentifier}`

**Response Codes:**
- `204 No Content`: Block created successfully
- `401 Unauthorized`: Invalid authentication credentials

**Example:**
```bash
curl -X POST \
     -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: a3f5d2e8..." \
     "https://api.example.com/api/create_block?extendedIdentifier=documents.report1&value=My%20report%20content"
```

---

### Get Blocks
**Endpoint:** `GET /get_blocks`  
**Authentication:** Required  
**Description:** Retrieve all blocks matching a path prefix under your namespace.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| extendedIdentifier | string | Yes | Path prefix to search (e.g., "documents") |

**Pattern Matching:** The search uses prefix matching. For example:
- `extendedIdentifier=documents` returns all blocks starting with `{env}.{username}.documents`
- This includes: `documents`, `documents.report1`, `documents.subfolder.item`, etc.

**Response:**
```json
{
  "blockList": [
    {
      "identifier": "prod.johndoe.documents.report1",
      "value": "Report content"
    },
    {
      "identifier": "prod.johndoe.documents.report2",
      "value": "Another report"
    }
  ]
}
```

**Response Codes:**
- `200 OK`: Blocks returned (may be empty list)
- `401 Unauthorized`: Invalid authentication credentials

**Example:**
```bash
curl -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: a3f5d2e8..." \
     "https://api.example.com/api/get_blocks?extendedIdentifier=documents"
```

---

### Update Block
**Endpoint:** `PATCH /update_block`  
**Authentication:** Required  
**Description:** Update the value of an existing block.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| extendedIdentifier | string | Yes | Path to the block to update |
| value | string | Yes | New content for the block |

**Response Codes:**
- `204 No Content`: Block updated successfully
- `401 Unauthorized`: Invalid authentication credentials

**Example:**
```bash
curl -X PATCH \
     -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: a3f5d2e8..." \
     "https://api.example.com/api/update_block?extendedIdentifier=documents.report1&value=Updated%20content"
```

---

### Delete Block
**Endpoint:** `POST /delete_block`  
**Authentication:** Required  
**Description:** Delete a block from your namespace.

**Note:** This only deletes the specific block, not child blocks in the hierarchy.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| extendedIdentifier | string | Yes | Path to the block to delete |

**Response Codes:**
- `204 No Content`: Block deleted successfully
- `401 Unauthorized`: Invalid authentication credentials

**Example:**
```bash
curl -X POST \
     -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: a3f5d2e8..." \
     "https://api.example.com/api/delete_block?extendedIdentifier=documents.report1"
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 204 | No Content | Successful operation with no response body |
| 401 | Unauthorized | Missing or invalid authentication credentials |
| 409 | Conflict | Resource already exists (e.g., duplicate username) |
| 422 | Unprocessable Entity | Invalid input format or validation error |
| 500 | Internal Server Error | Server-side error |

### Middleware Errors

**Authentication Required:**
```json
{
  "detail": "Authorization credentials required."
}
```

**Invalid Credentials:**
```json
{
  "detail": "Authorization credentials invalid."
}
```

---

## Interactive Documentation

The API provides interactive Swagger documentation at `/docs` when the server is running. This includes:
- Complete endpoint definitions
- Request/response schemas
- Try-it-out functionality
- Model documentation

Access it at: `https://api.example.com/api/docs`

---

## Data Models

### Environment
The system supports two environments:
- `prod`: Production environment
- `test`: Testing environment

### Unique Identifier Format
Format: `{environment}.{username}[.{path1}[.{path2}...]]`

Examples:
- `prod.johndoe` - User's root
- `prod.johndoe.documents` - Documents folder
- `test.testuser.data.item1` - Test user's data item

### Access Key Format
- 128-character hexadecimal string
- Generated using cryptographically secure random number generator
- Example: `a3f5d2e8c4b7f1d9...` (128 chars total)

---

## Rate Limiting

Currently, there are no rate limits enforced. However, it's recommended to:
- Batch operations when possible
- Cache access keys instead of logging in repeatedly
- Implement exponential backoff for failed requests

---

## Security Best Practices

1. **Store Access Keys Securely**
   - Never commit access keys to version control
   - Store in environment variables or secure key management systems

2. **Use HTTPS**
   - Always use HTTPS in production to protect credentials in transit

3. **Rotate Access Keys**
   - Periodically update your access key using the `/update_user` endpoint

4. **Password Security**
   - Use strong passwords
   - Never share passwords
   - Passwords are hashed using Argon2 before storage

5. **Validate User Input**
   - The API validates all inputs, but client applications should also validate
   - Sanitize data before displaying to users

---

## Example Workflows

### Complete User Registration and Data Storage Flow

```bash
# 1. Create a new user
curl -X POST "https://api.example.com/api/create_user?username=johndoe&email=john@example.com&password=pass123"

# 2. Login to get access key
ACCESS_KEY=$(curl "https://api.example.com/api/login?username=johndoe&password=pass123" | jq -r '.accessKey')

# 3. Create a data block
curl -X POST \
     -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: $ACCESS_KEY" \
     "https://api.example.com/api/create_block?extendedIdentifier=notes.meeting1&value=Meeting%20notes"

# 4. Retrieve blocks
curl -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: $ACCESS_KEY" \
     "https://api.example.com/api/get_blocks?extendedIdentifier=notes"

# 5. Update a block
curl -X PATCH \
     -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: $ACCESS_KEY" \
     "https://api.example.com/api/update_block?extendedIdentifier=notes.meeting1&value=Updated%20notes"

# 6. Delete a block
curl -X POST \
     -H "RequesterUsername: johndoe" \
     -H "RequesterAccessKey: $ACCESS_KEY" \
     "https://api.example.com/api/delete_block?extendedIdentifier=notes.meeting1"
```

---

## Support and Contact

For issues, questions, or feature requests, please contact the maintainers or open an issue in the repository.

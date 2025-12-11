# API Contract Testing

## Overview

Contract testing ensures that API providers and consumers adhere to a shared contract, preventing integration failures. It validates that APIs meet their specifications and that clients can consume them correctly.

## Contract Testing Types

### 1. Provider Contract Testing

**Verify API Implementation:**
- API matches specification
- All endpoints work as documented
- Response formats are correct
- Status codes are appropriate

### 2. Consumer Contract Testing

**Verify Client Implementation:**
- Client can parse responses
- Client handles all response codes
- Client sends correct requests
- Client validates responses

## OpenAPI/Swagger Contract Testing

### Generate Tests from OpenAPI

**Using Dredd:**
```yaml
# api.yaml
openapi: 3.0.0
paths:
  /users/{id}:
    get:
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
```

```bash
# Test API against spec
dredd api.yaml http://localhost:8000
```

### Schema Validation

**Validate Responses:**
```python
from openapi_spec_validator import validate_spec
from openapi_spec_validator.readers import read_from_filename

spec_dict, spec_url = read_from_filename('api.yaml')
validate_spec(spec_dict)

# Validate response against schema
from jsonschema import validate

response_schema = spec_dict['paths']['/users/{id}']['get']['responses']['200']['content']['application/json']['schema']
validate(instance=response.json(), schema=response_schema)
```

## Pact Contract Testing

### Provider Test

**Verify Provider:**
```python
from pact import Verifier

verifier = Verifier(
    provider='UserService',
    provider_base_url='http://localhost:8000'
)

output, _ = verifier.verify_pacts(
    'pacts/user_service-client.json',
    verbose=True
)
```

### Consumer Test

**Define Pact:**
```python
from pact import Consumer, Provider

pact = Consumer('ClientApp').has_pact_with(Provider('UserService'))

def test_get_user():
    expected = {
        'id': 123,
        'name': 'John Doe',
        'email': 'john@example.com'
    }
    
    (pact
     .given('user exists')
     .upon_receiving('a request for user')
     .with_request('get', '/users/123')
     .will_respond_with(200, body=expected))
    
    with pact:
        result = requests.get('http://localhost:8000/users/123')
        assert result.json() == expected

pact.write_to_file('pacts/user_service-client.json')
```

## JSON Schema Validation

### Request Validation

**Validate Request Body:**
```python
from jsonschema import validate, ValidationError

user_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer", "minimum": 0}
    },
    "required": ["name", "email"]
}

def validate_create_user_request(data):
    try:
        validate(instance=data, schema=user_schema)
        return True, None
    except ValidationError as e:
        return False, e.message
```

### Response Validation

**Validate Response:**
```python
user_response_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"}
    },
    "required": ["id", "name", "email", "created_at"]
}

def validate_user_response(response_data):
    try:
        validate(instance=response_data, schema=user_response_schema)
        return True
    except ValidationError:
        return False
```

## Contract Testing Strategies

### 1. Consumer-Driven Contracts

**Consumers Define Contracts:**
- Consumers write contract tests
- Providers verify against contracts
- Prevents breaking changes

### 2. Provider-Driven Contracts

**Providers Define Contracts:**
- OpenAPI/Swagger specs
- Consumers generate clients
- Versioned contracts

### 3. Bi-Directional Contracts

**Both Sides Verify:**
- Providers verify implementation
- Consumers verify consumption
- Shared contract definition

## Best Practices

1. **Version contracts:** Track contract versions
2. **Test regularly:** In CI/CD pipeline
3. **Fail fast:** Detect breaking changes early
4. **Document changes:** Clear changelogs
5. **Backward compatibility:** Support multiple versions
6. **Automate:** Integrate into build process
7. **Validate all fields:** Don't ignore optional fields
8. **Test error cases:** Error responses too
9. **Share contracts:** Provider and consumer access
10. **Monitor changes:** Alert on contract violations

## Tools

### Open Source
- **Dredd:** API blueprint testing
- **Pact:** Consumer-driven contracts
- **Schemathesis:** Property-based testing
- **REST Assured:** Java API testing

### Commercial
- **Pactflow:** Pact testing platform
- **Stoplight:** API design and testing
- **Postman:** API testing and contracts


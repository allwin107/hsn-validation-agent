# API Documentation

## Overview

The HSN Code Validation Agent provides a comprehensive RESTful API for validating Harmonized System Nomenclature (HSN) codes. The API supports single validation, batch processing, conversational interfaces, and administrative functions.

**Base URL**: `http://localhost:5000` (development)  
**Content-Type**: `application/json`  
**API Version**: v1.0

## Authentication

Currently, the API does not require authentication for basic validation endpoints. Administrative endpoints may implement authentication in future versions.

## Rate Limiting

- **Standard endpoints**: 1000 requests per minute
- **Batch endpoints**: 100 requests per minute
- **Admin endpoints**: 50 requests per minute

## Endpoints

### 1. Single HSN Code Validation

Validates a single HSN code against the master dataset.

**Endpoint**: `POST /validate`

#### Request

```json
{
  "hsn_code": "01012100"
}
```

#### Response - Valid Code

```json
{
  "valid": true,
  "description": "LIVE HORSES, ASSES, MULES AND HINNIES PURE-BRED BREEDING ANIMALS HORSES",
  "hierarchy": {
    "01": "LIVE ANIMALS",
    "0101": "LIVE HORSES, ASSES, MULES AND HINNIES",
    "010121": "PURE-BRED BREEDING ANIMALS"
  }
}
```

#### Response - Invalid Code

```json
{
  "valid": false,
  "reason": "HSN code not found"
}
```

#### Response - Format Error

```json
{
  "valid": false,
  "reason": "Invalid length: 3 (expected: 2,4,6,8)"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:5000/validate \
  -H "Content-Type: application/json" \
  -d '{"hsn_code": "01012100"}'
```

---

### 2. Batch HSN Code Validation

Validates multiple HSN codes in a single request.

**Endpoint**: `POST /validate_list`

#### Request

```json
{
  "hsn_list": ["0101", "1001", "99999999"]
}
```

#### Response

```json
{
  "results": [
    {
      "hsn_code": "0101",
      "valid": true,
      "description": "LIVE HORSES, ASSES, MULES AND HINNIES",
      "hierarchy": {
        "01": "LIVE ANIMALS"
      }
    },
    {
      "hsn_code": "1001",
      "valid": true,
      "description": "WHEAT AND MESLIN",
      "hierarchy": {
        "10": "CEREALS"
      }
    },
    {
      "hsn_code": "99999999",
      "valid": false,
      "reason": "HSN code not found"
    }
  ],
  "summary": {
    "total": 3,
    "valid": 2,
    "invalid": 1
  }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:5000/validate_list \
  -H "Content-Type: application/json" \
  -d '{"hsn_list": ["0101", "1001", "99999999"]}'
```

---

### 3. Conversational Interface

Processes natural language input to extract and validate HSN codes.

**Endpoint**: `POST /chat`

#### Request

```json
{
  "message": "Can you check if HSN code 01012100 is valid?"
}
```

#### Response

```json
{
  "reply": "✅ 01012100 is valid: LIVE HORSES, ASSES, MULES AND HINNIES PURE-BRED BREEDING ANIMALS HORSES\n🔗 Hierarchy:\n- 01: LIVE ANIMALS\n- 0101: LIVE HORSES, ASSES, MULES AND HINNIES",
  "extracted_codes": ["01012100"],
  "results": [
    {
      "hsn_code": "01012100",
      "valid": true,
      "description": "LIVE HORSES, ASSES, MULES AND HINNIES PURE-BRED BREEDING ANIMALS HORSES"
    }
  ]
}
```

#### Multiple Codes Example

**Request**:
```json
{
  "message": "Tell me about codes 0101 and 99999999"
}
```

**Response**:
```json
{
  "reply": "✅ 0101 is valid: LIVE HORSES, ASSES, MULES AND HINNIES\n❌ 99999999 is invalid: HSN code not found",
  "extracted_codes": ["0101", "99999999"],
  "results": [
    {
      "hsn_code": "0101",
      "valid": true,
      "description": "LIVE HORSES, ASSES, MULES AND HINNIES"
    },
    {
      "hsn_code": "99999999",
      "valid": false,
      "reason": "HSN code not found"
    }
  ]
}
```

#### cURL Example

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check HSN codes 0101 and 1001"}'
```

---

### 4. Dataset Reload

Dynamically reloads the HSN master dataset without service restart.

**Endpoint**: `POST /reload_dataset`

#### Request

```json
{}
```

#### Response - Success

```json
{
  "status": "Dataset reloaded successfully",
  "timestamp": "2025-05-26T10:30:00Z",
  "records_loaded": 12450
}
```

#### Response - Error

```json
{
  "error": "Dataset file not found: HSN_SAC.xlsx",
  "timestamp": "2025-05-26T10:30:00Z"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:5000/reload_dataset \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 5. Health Check

Returns the current health status of the API service.

**Endpoint**: `GET /health`

#### Response

```json
{
  "status": "healthy",
  "timestamp": "2025-05-26T10:30:00Z",
  "version": "1.0.0",
  "dataset": {
    "loaded": true,
    "records": 12450,
    "last_updated": "2025-05-26T09:00:00Z"
  },
  "performance": {
    "avg_response_time_ms": 45,
    "requests_per_minute": 120
  }
}
```

#### cURL Example

```bash
curl -X GET http://localhost:5000/health
```

---

### 6. Analytics Dashboard (Admin)

Returns analytics data about invalid HSN code attempts.

**Endpoint**: `GET /admin/invalids`

#### Response (HTML)

Returns an HTML dashboard with:
- Most frequently queried invalid codes
- Format error patterns
- Data quality insights
- Performance metrics

#### Response (JSON)

Add `Accept: application/json` header for JSON response:

```json
{
  "invalid_attempts": [
    {
      "pattern": "HSN code not found | 99999999",
      "count": 15
    },
    {
      "pattern": "Invalid length: 3 | 123",
      "count": 8
    }
  ],
  "total_invalid_attempts": 23,
  "most_common_errors": [
    "HSN code not found",
    "Invalid length",
    "Non-numeric characters detected"
  ]
}
```

#### cURL Example

```bash
# HTML Dashboard
curl -X GET http://localhost:5000/admin/invalids

# JSON Data
curl -X GET http://localhost:5000/admin/invalids \
  -H "Accept: application/json"
```

---

## Error Handling

All endpoints follow consistent error response format:

### HTTP Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Endpoint not found
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2025-05-26T10:30:00Z",
  "details": {
    "field": "hsn_code",
    "message": "HSN code must be 2, 4, 6, or 8 digits"
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_FORMAT` | HSN code format is invalid |
| `CODE_NOT_FOUND` | HSN code not found in dataset |
| `BATCH_SIZE_EXCEEDED` | Too many codes in batch request |
| `DATASET_NOT_LOADED` | Master dataset is not available |
| `INVALID_JSON` | Request body is not valid JSON |

---

## Validation Rules

### HSN Code Format

1. **Numeric Only**: Must contain only digits (0-9)
2. **Valid Lengths**: Must be exactly 2, 4, 6, or 8 digits
3. **Leading Zeros**: Preserved and significant
4. **No Special Characters**: Letters, spaces, or symbols not allowed

### Hierarchy Validation

The API validates hierarchical relationships:
- 8-digit codes must have valid 6-digit parents
- 6-digit codes must have valid 4-digit parents  
- 4-digit codes must have valid 2-digit parents

### Batch Processing Limits

- **Maximum batch size**: 100 codes per request
- **Request timeout**: 30 seconds
- **Memory limit**: Optimized for datasets up to 100K records

---

## Examples by Use Case

### E-commerce Integration

```javascript
// Validate product HSN code before listing
const validateProductHSN = async (hsnCode) => {
  const response = await fetch('/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hsn_code: hsnCode })
  });
  
  const result = await response.json();
  return result.valid;
};
```

### Bulk Import Validation

```python
import requests

def validate_bulk_hsn_codes(codes_list):
    response = requests.post(
        'http://localhost:5000/validate_list',
        json={'hsn_list': codes_list}
    )
    return response.json()

# Usage
codes = ['0101', '1001', '2202', '99999999']
results = validate_bulk_hsn_codes(codes)
```

### Chatbot Integration

```javascript
// Integrate with chatbot for natural language processing
const processChatMessage = async (userMessage) => {
  const response = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: userMessage })
  });
  
  const result = await response.json();
  return result.reply;
};
```

---

## Performance Optimization

### Caching

Validation results are cached for improved performance:
- **Cache Duration**: 1 hour for valid codes
- **Cache Key**: HSN code + dataset version
- **Cache Invalidation**: Automatic on dataset reload

### Batch Processing

For optimal performance:
- Group related codes in single batch request
- Use batch endpoint for 10+ codes
- Implement client-side caching for repeated queries

### Rate Limiting Best Practices

- Implement exponential backoff for rate limit errors
- Use batch endpoints to reduce request count
- Cache results on client side when possible

---


## SDK Libraries

Official SDKs available for:
- **Python**: `pip install hsn-validator-sdk`
- **JavaScript/Node.js**: `npm install hsn-validator-sdk`
- **Java**: Maven dependency available

---

## Support

- **API Issues**: [GitHub Issues](https://github.com/allwin107/hsn-validation-agent/issues)

---

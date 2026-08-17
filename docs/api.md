# 🔌 API Reference

Complete API documentation for AI Data Analyst.

## Base URL

**Development:** `http://localhost:8000`

**Interactive Docs:** `http://localhost:8000/docs`

## Authentication

Currently no authentication. For production, add API key authentication (see roadmap).

## Endpoints

### Health Check

Check if the service is running.

**`GET /health`**

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-08-17T10:30:00",
  "environment": "development",
  "model": "openai/gpt-4o-mini",
  "tools_available": [
    "safe_run_sql",
    "list_tables",
    "describe_table",
    "get_relationships",
    "create_chart"
  ]
}
```

**Status Codes:**
- `200` — Service healthy
- `500` — Service unhealthy

---

### Chat

Send a natural language question to the agent.

**`POST /api/chat`**

**Request Body:**
```json
{
  "message": "Show me top 5 products by revenue",
  "reset_context": false
}
```

**Parameters:**
- `message` (string, required) — Natural language question (1-2000 chars)
- `reset_context` (boolean, optional) — Clear conversation history before this query (default: false)

**Response:**
```json
{
  "response": "Here are the top 5 products by revenue...",
  "iterations": 3,
  "duration_ms": 2450.5,
  "tools_used": ["safe_run_sql", "create_chart"],
  "charts_generated": [
    "/charts/bar_Top_5_Products_20260817_103015.png"
  ],
  "tool_calls": [
    {
      "tool_name": "safe_run_sql",
      "duration_ms": 45.2,
      "iteration": 1,
      "success": true
    },
    {
      "tool_name": "create_chart",
      "duration_ms": 210.8,
      "iteration": 2,
      "success": true
    }
  ],
  "warnings": []
}
```

**Response Fields:**
- `response` — Agent's answer (markdown-formatted)
- `iterations` — Number of LLM iterations used
- `duration_ms` — Total time in milliseconds
- `tools_used` — Unique tool names called
- `charts_generated` — URLs to generated charts
- `tool_calls` — Detailed tool call info
- `warnings` — Any safety warnings

**Status Codes:**
- `200` — Success
- `400` — Invalid request
- `500` — Agent error

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many customers do we have?"
  }'
```

---

### Reset Conversation

Clear conversation history.

**`POST /api/reset`**

**Request:** No body

**Response:**
```json
{
  "status": "reset",
  "message": "Conversation reset"
}
```

---

### Get Database Schema

Retrieve database schema information.

**`GET /api/schema`**

**Response:**
```json
{
  "schema": "public",
  "table_count": 5,
  "tables": [
    {
      "table_name": "categories",
      "column_count": 3
    },
    {
      "table_name": "customers",
      "column_count": 7
    },
    ...
  ]
}
```

---

### Get Example Queries

Retrieve example queries organized by category.

**`GET /api/examples`**

**Response:**
```json
{
  "examples": [
    {
      "category": "Simple Analytics",
      "queries": [
        "How many customers do we have?",
        "What's our total revenue?"
      ]
    },
    ...
  ]
}
```

---

### Static Files

Charts are served as static files.

**`GET /charts/{filename}`**

**Example:**
`GET /charts/bar_Top_5_Products_20260817_103015.png`

Returns the PNG image.

---

## Error Responses

All errors follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {}
}
```

**Common Error Codes:**
- `unsafe_query` — Query rejected by safety validator
- `query_too_expensive` — Query cost too high
- `query_timeout` — Query took too long
- `postgresql_error` — Database error
- `agent_error` — LLM/agent error
- `internal_server_error` — Unexpected server error

---

## Rate Limiting

Currently no rate limiting. For production:
- Consider per-IP limits
- LLM cost tracking
- Query complexity limits

---

## Response Times

Typical response times:
- **Simple query:** 1-2 seconds
- **Query with chart:** 2-3 seconds
- **Complex multi-step:** 3-5 seconds
- **Schema exploration:** +1 iteration each

---

## Programming Examples

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={"message": "Show top 5 products"}
)
data = response.json()
print(data["response"])

# Download charts
for chart_url in data["charts_generated"]:
    chart = requests.get(f"http://localhost:8000{chart_url}")
    with open("chart.png", "wb") as f:
        f.write(chart.content)
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: 'Show top 5 products'})
});
const data = await response.json();
console.log(data.response);
```

### cURL
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How many customers?"}'
```

---

## OpenAPI Specification

Full OpenAPI spec available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Raw JSON: http://localhost:8000/openapi.json

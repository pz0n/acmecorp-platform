# Incident 001: Slow Order Requests

## Summary

Requests to the slow-order test endpoint experienced approximately 1.5 seconds of additional latency.

The incident was traced to a simulated legacy inventory dependency.

## Impact

Affected endpoint:

`GET /debug/slow-order/{order_id}`

Observed behavior:

- HTTP requests completed successfully
- Response latency increased to approximately 1.5 seconds
- Database access remained fast
- No increase in application errors was observed

## Detection

The issue was detected through application latency.

Structured request logs showed request durations of approximately 1500 ms.

Example:

```json
{
  "method": "GET",
  "path": "/debug/slow-order/1",
  "status_code": 200,
  "duration_ms": 1504.2
}

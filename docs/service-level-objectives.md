# Service Level Indicators and Objectives

AcmeCorp uses service-level indicators (SLIs) to describe the platform from the
customer's perspective rather than relying only on infrastructure health.

The objectives below are illustrative targets for the portfolio environment.
They are not based on historical production traffic.

## Service Indicators

### Orders Availability

**Question:** Can customers successfully interact with the Orders API?

The SLI measures the proportion of Orders API requests that do not return a
server-side 5xx response.

```promql
100 *
sum(
  rate(
    acmecorp_http_requests_total{
      service_name="orders-api",
      http_response_status_code!~"5.."
    }[5m]
  )
)
/
sum(
  rate(
    acmecorp_http_requests_total{
      service_name="orders-api"
    }[5m]
  )
)
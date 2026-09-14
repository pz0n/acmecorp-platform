# Incident 002 — Payment Authorization Failures

## Summary

Checkout requests experienced an elevated failure rate due to simulated failures in the Payments API.

The Orders API remained available, but requests requiring payment authorization intermittently failed.

---

## Customer Impact

Customers attempting checkout experienced intermittent HTTP 502 responses.

Order retrieval and other non-payment functionality remained available.

---

## Detection

The issue was first visible through the Orders API Grafana dashboard.

Observed signals:

- request volume remained normal
- 5xx error rate increased
- request latency remained relatively stable

This indicated an availability/error problem rather than a latency problem.

---

## Investigation

Structured Orders logs showed repeated downstream payment failures.

Example symptom:

```text
Payments API returned an error
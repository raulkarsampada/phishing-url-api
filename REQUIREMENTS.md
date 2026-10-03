# Requirements

**Problem:** Phishing links cause large financial losses. Users need a quick way to check a URL.

**Users:** Developers, security teams, and end users via a REST API.

**Functional requirements**
- POST /check-url accepts a URL and returns risk score (0-1), verdict, and red flags
- GET /health returns service status
- GET /model-info returns training metrics

**Non-functional requirements**
- Response time under 200 ms
- Never visits the URL (feature extraction only, safe by design)
- Invalid input returns HTTP 422

**Success criteria:** precision and recall >= 0.90 on the test split; all tests pass in CI.
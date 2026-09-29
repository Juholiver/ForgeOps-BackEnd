from fastapi.testclient import TestClient

from app.infrastructure.ssrf import SSRFProtection


def test_ssrf_blocks_localhost():
    safe, reason = SSRFProtection.is_safe_url("http://localhost:8080")
    assert safe is False
    assert "localhost" in reason


def test_ssrf_blocks_127_0_0_1():
    safe, reason = SSRFProtection.is_safe_url("http://127.0.0.1:8080")
    assert safe is False
    assert "Loopback" in reason


def test_ssrf_blocks_private_ip():
    safe, reason = SSRFProtection.is_safe_url("http://192.168.1.1:8080")
    assert safe is False
    assert "Private" in reason


def test_ssrf_blocks_10_x():
    safe, reason = SSRFProtection.is_safe_url("http://10.0.0.1:8080")
    assert safe is False
    assert "Private" in reason


def test_ssrf_blocks_172_16_x():
    safe, reason = SSRFProtection.is_safe_url("http://172.16.0.1:8080")
    assert safe is False
    assert "Private" in reason


def test_ssrf_blocks_metadata():
    safe, reason = SSRFProtection.is_safe_url("http://169.254.169.254/latest/meta-data")
    assert safe is False
    assert "Link-local" in reason


def test_ssrf_blocks_metadata_google():
    safe, reason = SSRFProtection.is_safe_url("http://metadata.google.internal/computeMetadata/v1/")
    assert safe is False
    assert "metadata" in reason


def test_ssrf_allows_public_url():
    safe, reason = SSRFProtection.is_safe_url("https://www.google.com")
    assert safe is True
    assert reason == ""


def test_ssrf_blocks_invalid_url():
    safe, reason = SSRFProtection.is_safe_url("not-a-url")
    assert safe is False


def test_security_headers_present(client: TestClient):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers

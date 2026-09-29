from dataclasses import dataclass

import httpx

from app.infrastructure.ssrf import SSRFProtection


@dataclass
class CheckResultData:
    status: str
    http_status: int | None
    response_time_ms: float | None
    error_message: str | None


class HealthCheckClient:
    async def check(self, url: str, method: str, timeout_seconds: int) -> CheckResultData:
        is_safe, reason = SSRFProtection.is_safe_url(url)
        if not is_safe:
            return CheckResultData(
                status="error",
                http_status=None,
                response_time_ms=None,
                error_message=f"SSRF protection: {reason}",
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    timeout=timeout_seconds,
                    follow_redirects=True,
                )
                return CheckResultData(
                    status="up",
                    http_status=response.status_code,
                    response_time_ms=response.elapsed.total_seconds() * 1000,
                    error_message=None,
                )
        except httpx.TimeoutException:
            return CheckResultData(
                status="timeout",
                http_status=None,
                response_time_ms=None,
                error_message=f"Request timed out after {timeout_seconds}s",
            )
        except httpx.HTTPStatusError as e:
            return CheckResultData(
                status="error",
                http_status=e.response.status_code,
                response_time_ms=None,
                error_message=str(e),
            )
        except Exception as e:
            return CheckResultData(
                status="error",
                http_status=None,
                response_time_ms=None,
                error_message=str(e),
            )

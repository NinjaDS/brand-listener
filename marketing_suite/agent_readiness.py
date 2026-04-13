"""
Agent readiness pre-flight checks.
"""

import os


def check_readiness() -> dict:
    """
    Run pre-flight checks and return readiness status.

    Returns:
        {
            "ready": bool,
            "checks": {name: "pass" | "fail"},
            "warnings": [str]
        }
    """
    checks = {}
    warnings = []

    # Check LINKDAPI_KEY
    if os.environ.get("LINKDAPI_KEY", "").strip():
        checks["LINKDAPI_KEY"] = "pass"
    else:
        checks["LINKDAPI_KEY"] = "fail"
        warnings.append("LINKDAPI_KEY not set — LinkedIn scraping will be skipped")

    # Check AWS_DEFAULT_REGION
    if os.environ.get("AWS_DEFAULT_REGION", "").strip():
        checks["AWS_DEFAULT_REGION"] = "pass"
    else:
        checks["AWS_DEFAULT_REGION"] = "fail"
        warnings.append("AWS_DEFAULT_REGION not set — Bedrock LLM Council will be unavailable")

    # Check boto3
    try:
        import boto3  # noqa: F401
        checks["boto3"] = "pass"
    except ImportError:
        checks["boto3"] = "fail"
        warnings.append("boto3 not installed — Bedrock LLM Council will be unavailable")

    ready = all(v == "pass" for v in checks.values())

    return {
        "ready": ready,
        "checks": checks,
        "warnings": warnings,
    }

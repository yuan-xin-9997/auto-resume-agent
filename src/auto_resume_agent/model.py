import math


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def usage(value):
    result = {"available": None, "reset_at": None, "windows": []}
    if not isinstance(value, dict):
        return result
    buckets = value.get("rateLimitsByLimitId")
    if not isinstance(buckets, dict) or not buckets:
        buckets = {"codex": value.get("rateLimits")}
    blocked, unknown, explicit = [], False, value.get("ordinaryUsageAllowed") is False
    for key, bucket in buckets.items():
        if not isinstance(bucket, dict):
            unknown = True
            continue
        explicit |= bucket.get("spendControlReached") is True or bucket.get("rateLimitReachedType") is not None
        for name in ("primary", "secondary"):
            window = bucket.get(name)
            if window is None:
                continue
            if not isinstance(window, dict) or not numeric(window.get("usedPercent")) or window["usedPercent"] < 0:
                unknown = True
                continue
            reset = window.get("resetsAt")
            reset = reset if numeric(reset) and reset > 0 else None
            row = {"bucket": key, "window": name, "used_percent": window["usedPercent"],
                   "reset_at": reset, "minutes": window.get("windowDurationMins")}
            result["windows"].append(row)
            if row["used_percent"] >= 100:
                blocked.append(reset)
    if blocked or explicit:
        result["available"] = False
        if blocked and all(x is not None for x in blocked) and not explicit:
            result["reset_at"] = max(blocked)
    elif result["windows"] and not unknown:
        result["available"] = True
    return result


def category(turn):
    if not isinstance(turn, dict) or turn.get("status") != "failed":
        return None
    error = turn.get("error")
    if not isinstance(error, dict):
        return None
    info = error.get("codexErrorInfo")
    detail = {}
    if isinstance(info, dict) and len(info) == 1:
        code, detail = next(iter(info.items()))
        detail = detail if isinstance(detail, dict) else {}
    elif isinstance(info, str):
        code = info
    else:
        return None
    # Terminal structured errors always win over a nested status or message.
    mapping = {"usageLimitExceeded": "usage_limit", "rateLimitExceeded": "rate_limit",
               "serverOverloaded": "server_error", "internalServerError": "server_error",
               "httpConnectionFailed": "network", "responseStreamConnectionFailed": "network",
               "responseStreamDisconnected": "stream"}
    if code not in mapping:
        return None
    status = detail.get("httpStatusCode")
    if numeric(status) and 400 <= status < 500 and status not in (408, 425, 429):
        return None
    return mapping[code]


def delay(attempt):
    return min(300, 15 * 2 ** min(attempt, 5))


def next_delay(now, due, normal=5):
    """Wall clock deadlines survive sleep; no long fixed polling interval."""
    return max(0.25, min(normal, due - now)) if due is not None else normal

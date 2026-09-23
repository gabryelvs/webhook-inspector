"""Work out which client actually sent a request.

Request capture (the recorded source IP) and the bin-creation rate limiter both
use this, so they can't disagree about who a client is.
"""

from starlette.requests import Request

# Longest textual IP address (IPv4-mapped IPv6); also the source_ip column width.
MAX_IP_LENGTH = 45


def client_ip(request: Request) -> str | None:
    # In production every connection ends at Fly's proxy, so request.client is
    # the proxy, not the visitor. Fly's proxy sets Fly-Client-IP to the address
    # it accepted the connection from, overwriting any value the client sent,
    # so that header is trusted. This only holds because Fly's proxy is the
    # app's sole public ingress; exposed directly, the header would be forgeable.
    #
    # X-Forwarded-For is deliberately ignored. Its leftmost entry is whatever
    # the client chose to send, so trusting it would let anyone forge their
    # recorded IP and dodge the rate limit by rotating the value. Picking the
    # entry a trusted proxy appended instead means hard-coding how many proxy
    # hops sit in front of the app, and Fly-Client-IP already gives us that
    # address without the guesswork. With no Fly proxy in front (local dev)
    # we fall back to the socket peer.
    fly_ip = request.headers.get("fly-client-ip")
    if fly_ip:
        return fly_ip[:MAX_IP_LENGTH]
    return request.client.host if request.client else None


def rate_limit_key(request: Request) -> str:
    # slowapi needs a string key; requests with no known peer share one bucket.
    return client_ip(request) or "unknown"

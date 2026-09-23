"""Work out which client actually sent a request.

Request capture (the recorded source IP) and the bin-creation rate limiter both
use this, so they can't disagree about who a client is.
"""

import os

from starlette.requests import Request

# Longest textual IP address (IPv4-mapped IPv6); also the source_ip column width.
MAX_IP_LENGTH = 45


def client_ip(request: Request) -> str | None:
    # Only the header set by whichever proxy actually fronts this deployment
    # is trusted, and only while that proxy is the app's sole public ingress
    # (elsewhere, a header like this would be client-forgeable). Everything
    # else falls back to the socket peer.
    #
    # On Vercel (VERCEL is set at runtime) every connection ends at Vercel's
    # edge network, which sets x-real-ip to the client address it accepted
    # the connection from, overwriting any value the client sent. See
    # https://vercel.com/docs/headers/request-headers. Off Vercel, x-real-ip
    # is just another client-supplied header and must not be trusted — a
    # request without the matching proxy in front could forge it to dodge
    # the rate limit.
    if os.environ.get("VERCEL"):
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip[:MAX_IP_LENGTH]
    else:
        # In production (off Vercel) every connection ends at Fly's proxy, so
        # request.client is the proxy, not the visitor. Fly's proxy sets
        # Fly-Client-IP to the address it accepted the connection from,
        # overwriting any value the client sent, so that header is trusted
        # here.
        #
        # X-Forwarded-For is deliberately ignored. Its leftmost entry is
        # whatever the client chose to send, so trusting it would let anyone
        # forge their recorded IP and dodge the rate limit by rotating the
        # value. Picking the entry a trusted proxy appended instead means
        # hard-coding how many proxy hops sit in front of the app, and
        # Fly-Client-IP already gives us that address without the guesswork.
        fly_ip = request.headers.get("fly-client-ip")
        if fly_ip:
            return fly_ip[:MAX_IP_LENGTH]

    # No proxy header for the current environment (e.g. local dev, or the
    # header was simply absent): fall back to the socket peer.
    return request.client.host if request.client else None


def rate_limit_key(request: Request) -> str:
    # slowapi needs a string key; requests with no known peer share one bucket.
    return client_ip(request) or "unknown"

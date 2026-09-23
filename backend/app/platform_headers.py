"""Drop headers the hosting platform adds, so a bin shows what the sender sent.

On Vercel, the edge network adds its own request headers before the app sees
them: `x-vercel-*` (request id, and the sender's approximate city, region and
latitude/longitude) plus `x-real-ip`, `x-forwarded-*` and `forwarded`, which it sets
with its own values. See https://vercel.com/docs/headers/request-headers.
Stored as-is, they would look like part of the webhook and would expose the
sender's rough location to whoever holds the bin URL.

Off Vercel nothing is stripped: there, any such header was sent by the client
itself, and showing exactly what arrived is the whole point of the tool.
The client IP is still recorded separately, before stripping (see client_ip).
"""

from collections.abc import Mapping

_VERCEL_ADDED = {
    "x-real-ip",
    "x-forwarded-for",
    "x-forwarded-host",
    "x-forwarded-proto",
    "x-forwarded-port",
    "forwarded",  # RFC 7239; Vercel adds it with the client address
}


def strip_platform_headers(headers: Mapping[str, str], on_vercel: bool) -> dict[str, str]:
    if not on_vercel:
        return dict(headers)
    return {
        name: value
        for name, value in headers.items()
        if not name.lower().startswith("x-vercel-") and name.lower() not in _VERCEL_ADDED
    }

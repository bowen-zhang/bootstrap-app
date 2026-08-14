from connectrpc.request import RequestContext
from http.cookies import SimpleCookie
from typing import Optional


def _get_cookie(ctx: RequestContext, cookie_name: str) -> Optional[str]:
    raw_cookie_header = ctx.request_headers.get("cookie")
    if not raw_cookie_header:
        return None

    cookie = SimpleCookie()
    cookie.load(raw_cookie_header)
    if cookie_name not in cookie:
        return None

    return cookie[cookie_name].value


def _set_cookie(
    ctx: RequestContext,
    name: str, 
    value: str, 
    path: str = "/", 
    httponly: bool = True, 
    secure: bool = True, 
    samesite: str = "Strict", 
    max_age: Optional[int] = None
) -> None:
    cookie = SimpleCookie()
    cookie[name] = value
    
    # SimpleCookie requires lowercase attribute keys
    cookie[name]["path"] = path
    cookie[name]["httponly"] = httponly
    cookie[name]["secure"] = secure
    cookie[name]["samesite"] = samesite
    
    if max_age is not None:
        cookie[name]["max-age"] = max_age
        
    cookie = cookie[name].OutputString()
    ctx.response_headers.add("Set-Cookie", cookie)
    

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth.dependencies import resolve_optional_user

router = APIRouter(tags=["public-pages"])

SIGN_IN_URL = "http://localhost:8000/auth/login"


@router.get("/", response_class=HTMLResponse)
async def public_landing_page(
    request: Request,
    user=Depends(resolve_optional_user),
) -> HTMLResponse:
    if user is not None:
        return RedirectResponse(url="/dev/admin", status_code=303)
    return HTMLResponse(
        content=f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>QC Coversheets</title>
  <style>
    body {{
      font-family: "Segoe UI", sans-serif;
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f6f4ef;
      color: #1f1f1f;
    }}
    .card {{
      background: #ffffff;
      border-radius: 16px;
      padding: 36px 42px;
      max-width: 520px;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.08);
      text-align: center;
    }}
    .logo {{
      display: block;
      # height: 75%;
      max-height: 230px;
      width: auto;
      margin: 0 auto;
  }}    
    h1 {{
      margin: 0 0 12px 0;
      font-size: 1.9rem;
      letter-spacing: 0.02em;
    }}
    p {{
      margin: 0 0 24px 0;
      color: #4b4b4b;
      line-height: 1.5;
    }}
    .btn {{
      display: inline-block;
      padding: 12px 22px;
      border-radius: 999px;
      background: #0b57d0;
      color: #fff;
      text-decoration: none;
      font-weight: 600;
    }}
  </style>
</head>
<body>
  <div class="card">
    <img src="/static/images/logo.png" alt="Gresham Smith" class="logo">
    <h1>QC Coversheet Review</h1>
    <p>Sign in to access the internal QC checklist tools and reviewer workflows.</p>
    <a class="btn" href="{SIGN_IN_URL}">Sign In</a>
  </div>
</body>
</html>
""",
        status_code=200,
    )


@router.get("/logged-out", response_class=HTMLResponse)
async def logged_out_page() -> HTMLResponse:
    response = HTMLResponse(
        content=f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Signed Out</title>
  <style>
    body {{
      font-family: "Segoe UI", sans-serif;
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f6f4ef;
      color: #1f1f1f;
    }}
    .card {{
      background: #ffffff;
      border-radius: 16px;
      padding: 32px 40px;
      max-width: 520px;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.08);
      text-align: center;
    }}
    .logo {{
      display: block;
      # height: 75%;
      max-height: 230px;
      width: auto;
      margin: 0 auto;
  }}
    h1 {{
      margin: 0 0 10px 0;
      font-size: 1.7rem;
    }}
    p {{
      margin: 0 0 22px 0;
      color: #4b4b4b;
      line-height: 1.5;
    }}
    .btn {{
      display: inline-block;
      padding: 12px 22px;
      border-radius: 999px;
      background: #0b57d0;
      color: #fff;
      text-decoration: none;
      font-weight: 600;
    }}
  </style>
</head>
<body>
  <div class="card">
     <img src="/static/images/logo.png" alt="Gresham Smith" class="logo">
    <h1>You are signed out</h1>
    <p>Your session has ended. Sign in again when you are ready to continue.</p>
    <a class="btn" href="{SIGN_IN_URL}">Sign In</a>
  </div>
</body>
</html>
""",
        status_code=200,
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

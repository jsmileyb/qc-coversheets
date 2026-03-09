# Project Update

## Summary
Added a public landing page and a logged-out confirmation page, strengthened logout/session clearing, and tightened auth protection for HTML routes.

## Added

- Public landing page at `/` with a Sign In button.
- Logged-out confirmation page at `/logged-out`.

## Updated 

- Logout now clears full session state and deletes the session cookie.
- HTML navigation requests that hit protected routes redirect to the landing page.
- Protected HTML responses set no-store cache headers to prevent back-button access.
- Dev-page logout actions now redirect to `/logged-out`.

## Fixed

- Prevented re-entering protected pages after logout without re-authentication.

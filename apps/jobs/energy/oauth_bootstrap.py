#!/usr/bin/env python3
"""
One-time OAuth bootstrap for Enphase API.

Run locally to complete the OAuth flow and get initial tokens:

    python -m apps.jobs.energy.oauth_bootstrap

This will:
1. Open your browser to Enphase login
2. Start a temporary local server to catch the redirect
3. Exchange the auth code for tokens
4. Print the tokens for you to set as secrets
5. Optionally store them in the Postgres key_value_store
"""

import base64
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests

# Load from env
CLIENT_ID = os.getenv("ENPHASE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("ENPHASE_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8765/callback"
AUTH_URL = "https://api.enphaseenergy.com/oauth/authorize"
TOKEN_URL = "https://api.enphaseenergy.com/oauth/token"

_auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<h1>Authorization successful!</h1>"
                b"<p>You can close this window and return to the terminal.</p>"
            )
        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Error: No authorization code received</h1>")

    def log_message(self, format, *args):
        pass  # Suppress request logging


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Set ENPHASE_CLIENT_ID and ENPHASE_CLIENT_SECRET environment variables")
        sys.exit(1)

    # Build auth URL
    state = base64.urlsafe_b64encode(os.urandom(16)).decode()
    auth_url = (
        f"{AUTH_URL}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
    )

    # Start callback server BEFORE opening browser to avoid race condition
    server = HTTPServer(("localhost", 8765), CallbackHandler)
    print("Listening on http://localhost:8765/callback ...")

    print(f"\nOpening browser for Enphase authorization...")
    print(f"If the browser doesn't open, go to:\n{auth_url}\n")
    webbrowser.open(auth_url)
    server.handle_request()

    if not _auth_code:
        print("Error: No authorization code received")
        sys.exit(1)

    print(f"\nReceived auth code, exchanging for tokens...")

    # Exchange code for tokens
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    basic_auth = base64.b64encode(credentials.encode()).decode()

    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": _auth_code,
        },
    )

    if response.status_code != 200:
        print(f"Error: Token exchange failed: {response.status_code} {response.text}")
        sys.exit(1)

    tokens = response.json()

    print("\n" + "=" * 60)
    print("SUCCESS! Here are your tokens:")
    print("=" * 60)
    print(f"\nENPHASE_ACCESS_TOKEN={tokens['access_token']}")
    print(f"ENPHASE_REFRESH_TOKEN={tokens['refresh_token']}")
    print(f"\nToken expires in: {tokens['expires_in']} seconds")
    print("\nSet ENPHASE_REFRESH_TOKEN as a GitHub Actions secret.")
    print("The access token will be auto-refreshed by the collection job.")

    # Optionally store in DB
    db_url = os.getenv("DATABASE_URL", os.getenv("ENERGY_DATABASE_URL", ""))
    if db_url:
        try:
            from .db import Database
            db = Database(db_url)
            db.set_token("enphase_access_token", tokens["access_token"])
            db.set_token("enphase_refresh_token", tokens["refresh_token"])
            db.close()
            print("\nTokens also stored in Postgres key_value_store.")
        except Exception as e:
            print(f"\nCouldn't store in DB (optional): {e}")

    print("=" * 60)


if __name__ == "__main__":
    main()

"""One-time OAuth flow to obtain a GA4 refresh token."""

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
CLIENT_SECRETS = Path(__file__).resolve().parent.parent / "data" / "ga4-oauth-client.json"
TOKEN_PATH = Path(__file__).resolve().parent.parent / "data" / "ga4-token.json"


def main() -> None:
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
    creds = flow.run_local_server(port=8085, prompt="consent", access_type="offline")

    TOKEN_PATH.write_text(creds.to_json())
    print(f"Token saved to {TOKEN_PATH}")
    print("You can now use GA4 tools in the agent.")


if __name__ == "__main__":
    main()

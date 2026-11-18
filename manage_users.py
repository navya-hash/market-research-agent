#!/usr/bin/env python
"""
Helper script to add or manage users in config/auth.yaml.
Usage:
    python manage_users.py add <username> <password> <email> <first_name> <last_name> [role]
    python manage_users.py list
"""
import sys
import yaml
import pathlib
import streamlit_authenticator as stauth

AUTH_FILE = pathlib.Path("config/auth.yaml")


def load_auth_config():
    if not AUTH_FILE.exists():
        AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {
            "credentials": {"usernames": {}},
            "cookie": {
                "name": "market_research_auth_cookie",
                "key": "market_research_auth_secret_cookie_key_2026",
                "expiry_days": 30
            }
        }
    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"credentials": {"usernames": {}}}


def save_auth_config(config):
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False)


def add_user(username, password, email, first_name, last_name, role="user"):
    config = load_auth_config()
    hashed_pwd = stauth.Hasher.hash(password)
    config["credentials"]["usernames"][username] = {
        "email": email,
        "failed_login_attempts": 0,
        "first_name": first_name,
        "last_name": last_name,
        "logged_in": False,
        "password": hashed_pwd,
        "roles": [role]
    }
    save_auth_config(config)
    print(f"Successfully added/updated user '{username}' ({first_name} {last_name}) with role '{role}'.")


def list_users():
    config = load_auth_config()
    users = config.get("credentials", {}).get("usernames", {})
    if not users:
        print("No users configured.")
        return
    print(f"Found {len(users)} user(s):")
    for u, data in users.items():
        role = data.get("roles", ["user"])[0] if data.get("roles") else "user"
        print(f"  - Username: {u:15} | Name: {data.get('first_name', '')} {data.get('last_name', '')} | Email: {data.get('email', '')} | Role: {role}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "list":
        list_users()
    elif cmd == "add" and len(sys.argv) >= 7:
        role = sys.argv[7] if len(sys.argv) > 7 else "user"
        add_user(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], role)
    else:
        print(__doc__)

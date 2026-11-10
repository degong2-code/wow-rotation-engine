"""Owner-only local ChatGPT connection records (Unix / WSL pilot).

No credentials are ever written inside the public repository. On native
Windows use an OS credential vault adapter instead of this Unix-mode store.
Values remain user-local. No automatic token refresh/publishing on load.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import time

from .build import ROOT
from .chatgpt_oauth import (
    OAuthError, VerifiedConnection, fresh_host_id,
    HOST_UUID, ISSUED_ID, ISSUER,
)

DEFAULT_ROOT = Path.home() / ".config" / "wow-rotation-textbook" / "chatgpt"


class LocalAuthStore:
    def __init__(self, directory: Path = DEFAULT_ROOT):
        self.directory = Path(directory).expanduser().absolute()
        repository = ROOT.resolve()
        if self.directory == repository or self.directory.is_relative_to(repository):
            raise OAuthError("oauth_storage_inside_public_repository")
        if os.name != "posix":
            raise OAuthError("unix_store_requires_wsl_or_protected_os_keychain")
        self._prepare_dir()

    def _prepare_dir(self):
        folder = self.directory
        if folder.is_symlink():
            raise OAuthError("symlink_storage_directory")
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        st = folder.lstat()
        if (not stat.S_ISDIR(st.st_mode) or st.st_mode & 0o077
                or st.st_uid != os.getuid()):
            raise OAuthError("oauth_storage_directory_is_not_private")

    def _path(self, basename: str) -> Path:
        if not basename or "/" in basename or "\\" in basename or basename.startswith("."):
            raise OAuthError("invalid_account_filename")
        return self.directory / basename

    def _read(self, name: str) -> dict | None:
        file = self._path(name)
        try:
            st = file.lstat()
        except FileNotFoundError:
            return None
        if (not stat.S_ISREG(st.st_mode) or st.st_mode & 0o077
                or st.st_uid != os.getuid()):
            raise OAuthError("oauth_credentials_not_private")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(file, flags)
            with os.fdopen(fd, "rb") as stream:
                raw = stream.read(32769)
        except OSError:
            raise OAuthError("oauth_credentials_unreadable") from None
        if len(raw) > 32768:
            raise OAuthError("oauth_credentials_oversized")
        try:
            out = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError):
            raise OAuthError("oauth_credentials_corrupted") from None
        if not isinstance(out, dict):
            raise OAuthError("oauth_credentials_corrupted")
        return out

    def _write(self, name: str, value: dict):
        target = self._path(name)
        payload = (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        if len(payload) > 32768:
            raise OAuthError("oauth_credentials_oversized")
        temp = self.directory / ("auth-temp-" + secrets.token_hex(12))
        mode = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        mode |= getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(temp, mode, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, target)
        finally:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass

    def host_id(self) -> str:
        entry = self._read("host.json")
        if entry is None:
            host = fresh_host_id()
            self._write("host.json", {"host_id": host})
            return host
        host = entry.get("host_id")
        if not isinstance(host, str) or not HOST_UUID.fullmatch(host):
            raise OAuthError("invalid_stored_host_id")
        return host

    @staticmethod
    def _account_name(client_id: str) -> str:
        if not isinstance(client_id, str) or not ISSUED_ID.fullmatch(client_id):
            raise OAuthError("invalid_registered_client")
        return "account-" + hashlib.sha256(client_id.encode("utf-8")).hexdigest() + ".json"

    def save(self, connection: VerifiedConnection) -> None:
        if connection.host_id != self.host_id():
            raise OAuthError("host_id_changed_during_login")
        if not connection.subject or not ISSUED_ID.fullmatch(connection.client_id):
            raise OAuthError("invalid_verified_connection")
        t = connection.tokens
        self._write(self._account_name(connection.client_id), {
            "schema_version": "chatgpt-oauth-local-v1",
            "issuer": ISSUER, "subject": connection.subject,
            "client_id": connection.client_id, "host_id": connection.host_id,
            "email": connection.email,
            "access_token": t.access_token, "refresh_token": t.refresh_token,
            "id_token": t.id_token, "scopes": sorted(t.scopes),
            "expires_in": t.expires_in,
            "earliest_refresh_at": t.earliest_refresh_at,
            "saved_at": int(time.time()),
        })

    def read_for_reauthorization(self, client_id: str) -> dict | None:
        """Saved identity is only a login hint; no inference grant is returned."""
        account = self._read(self._account_name(client_id))
        if account is None:
            return None
        if (account.get("schema_version") != "chatgpt-oauth-local-v1"
                or account.get("issuer") != ISSUER
                or account.get("client_id") != client_id
                or account.get("host_id") != self.host_id()
                or not isinstance(account.get("subject"), str)
                or not account["subject"]):
            raise OAuthError("stored_registration_mismatch")
        return {
            "client_id": account["client_id"],
            "subject": account["subject"],
            "email": account.get("email"),
            "id_token_hint": account.get("id_token"),
        }

    def registered_client_ids(self) -> tuple[str, ...]:
        """Only checked, owner-readable local registrations are listed."""
        values = []
        for file in self.directory.glob("account-*.json"):
            if file.is_symlink():
                raise OAuthError("oauth_credentials_not_private")
            record = self._read(file.name)
            if record and record.get("client_id") and (
                file.name == self._account_name(record["client_id"])
            ):
                values.append(record["client_id"])
            else:
                raise OAuthError("stored_registration_mismatch")
        return tuple(sorted(values))

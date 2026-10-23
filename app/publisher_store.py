"""Private, per-browser storage for social connections and upload operations."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import time
from uuid import uuid4

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # Keep rendering usable before optional publishing deps are installed.
    Fernet = None
    InvalidToken = ValueError


class PublisherStore:
    """Persist upload state and encrypt provider credentials at rest.

    The application has no user accounts, so every row is scoped to an HMAC
    derived from a random id held in Flask's signed browser session.
    """

    def __init__(self, database_path, encryption_key, session_secret):
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError:
            pass
        try:
            self._fernet = Fernet(str(encryption_key).encode("ascii")) if encryption_key and Fernet else None
        except (ValueError, UnicodeError):
            self._fernet = None
        self._session_secret = str(session_secret).encode("utf-8")
        self.process_id = uuid4().hex
        self._initialize()
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    @property
    def encryption_ready(self):
        return self._fernet is not None

    @property
    def encryption_available(self):
        return Fernet is not None

    def owner_key(self, session_id):
        return hmac.new(self._session_secret, str(session_id).encode("utf-8"),
                        hashlib.sha256).hexdigest()

    @contextmanager
    def _db(self):
        connection = sqlite3.connect(self.path, timeout=20)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self):
        with self._db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS render_owners (
                    job_id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    project_id TEXT NOT NULL DEFAULT 'draft',
                    created_at REAL NOT NULL,
                    filename TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS social_accounts (
                    owner TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    secrets_blob BLOB NOT NULL,
                    external_id TEXT,
                    display_name TEXT,
                    scopes TEXT NOT NULL DEFAULT '',
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (owner, platform)
                );
                CREATE TABLE IF NOT EXISTS social_uploads (
                    id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    render_job_id TEXT NOT NULL,
                    project_id TEXT NOT NULL DEFAULT 'draft',
                    source_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0,
                    message TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    settings_json TEXT NOT NULL,
                    operation_blob BLOB,
                    external_id TEXT,
                    result_url TEXT,
                    error TEXT,
                    worker_id TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS social_uploads_owner_time
                    ON social_uploads(owner, created_at DESC);
                CREATE INDEX IF NOT EXISTS social_uploads_render_platform
                    ON social_uploads(owner, render_job_id, platform, created_at DESC);
            """)
            columns = {row["name"] for row in db.execute("PRAGMA table_info(social_uploads)").fetchall()}
            if "worker_id" not in columns:
                db.execute("ALTER TABLE social_uploads ADD COLUMN worker_id TEXT NOT NULL DEFAULT ''")
            if "project_id" not in columns:
                db.execute("ALTER TABLE social_uploads ADD COLUMN project_id TEXT NOT NULL DEFAULT 'draft'")
            render_columns = {row["name"] for row in db.execute("PRAGMA table_info(render_owners)").fetchall()}
            if "project_id" not in render_columns:
                db.execute("ALTER TABLE render_owners ADD COLUMN project_id TEXT NOT NULL DEFAULT 'draft'")
            if "filename" not in render_columns:
                db.execute("ALTER TABLE render_owners ADD COLUMN filename TEXT NOT NULL DEFAULT ''")
            if "metadata_json" not in render_columns:
                db.execute("ALTER TABLE render_owners ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'")

    def mark_interrupted_uploads(self):
        """Flag operations that belonged to a previous single-worker app process."""
        with self._db() as db:
            db.execute("""UPDATE social_uploads SET status='failed', phase='failed',
                          message='The app process stopped during this upload. Refresh provider status before retrying.',
                          error='Process interrupted.', updated_at=?
                          WHERE status IN ('queued','initializing','uploading','processing','cancelling')
                          AND worker_id != ?""", (time.time(), self.process_id))

    def register_render(self, job_id, owner, project_id="draft"):
        with self._db() as db:
            db.execute("INSERT OR REPLACE INTO render_owners(job_id, owner, project_id, created_at, filename, metadata_json) VALUES(?,?,?,?,'','{}')",
                       (str(job_id), str(owner), str(project_id), time.time()))

    def complete_render(self, job_id, owner, result):
        """Persist the small render snapshot needed to find and publish its MP4."""
        filename = str(result.get("filename") or "")
        if filename != f"{job_id}.mp4":
            raise ValueError("Completed render filename does not match its job ID.")
        fields = ("download_title", "download_url", "publish_metadata", "surah", "ayah_start",
                  "ayah_end", "reciter", "duration", "width", "height", "fps", "created_at")
        snapshot = {key: result[key] for key in fields if key in result}
        with self._db() as db:
            cursor = db.execute("UPDATE render_owners SET filename=?, metadata_json=? WHERE job_id=? AND owner=?",
                                (filename, json.dumps(snapshot, ensure_ascii=False), str(job_id), str(owner)))
            if cursor.rowcount != 1:
                raise ValueError("Render ownership record was not found.")

    def get_render(self, job_id, owner):
        with self._db() as db:
            row = db.execute("SELECT * FROM render_owners WHERE job_id=? AND owner=?",
                             (str(job_id), str(owner))).fetchone()
        return self._render_row(row) if row else None

    def list_renders(self, owner, *, limit=50):
        with self._db() as db:
            rows = db.execute("SELECT * FROM render_owners WHERE owner=? AND filename!='' ORDER BY created_at DESC LIMIT ?",
                              (str(owner), max(1, min(200, int(limit))))).fetchall()
        return [self._render_row(row) for row in rows]

    @staticmethod
    def _render_row(row):
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except (TypeError, ValueError):
            metadata = {}
        return {"render_job_id": row["job_id"], "project_id": row["project_id"] or "draft",
                "filename": row["filename"] or "", "metadata": metadata,
                "created_at": row["created_at"]}

    def render_project_id(self, job_id, owner):
        with self._db() as db:
            row = db.execute("SELECT project_id FROM render_owners WHERE job_id=? AND owner=?",
                             (str(job_id), str(owner))).fetchone()
        return row["project_id"] if row else "draft"

    def owns_render(self, job_id, owner):
        with self._db() as db:
            row = db.execute("SELECT 1 FROM render_owners WHERE job_id=? AND owner=?",
                             (str(job_id), str(owner))).fetchone()
        return row is not None

    def save_account(self, owner, platform, secrets, *, external_id="", display_name="", scopes=""):
        if self._fernet is None:
            raise RuntimeError("Set QURAN_REELS_TOKEN_ENCRYPTION_KEY before connecting an account.")
        encrypted = self._fernet.encrypt(json.dumps(secrets, separators=(",", ":")).encode("utf-8"))
        with self._db() as db:
            db.execute("""INSERT INTO social_accounts(owner,platform,secrets_blob,external_id,display_name,scopes,updated_at)
                          VALUES(?,?,?,?,?,?,?) ON CONFLICT(owner,platform) DO UPDATE SET
                          secrets_blob=excluded.secrets_blob, external_id=excluded.external_id,
                          display_name=excluded.display_name, scopes=excluded.scopes, updated_at=excluded.updated_at""",
                       (str(owner), str(platform), encrypted, str(external_id or ""),
                        str(display_name or ""), str(scopes or ""), time.time()))

    def get_account(self, owner, platform):
        with self._db() as db:
            row = db.execute("SELECT * FROM social_accounts WHERE owner=? AND platform=?",
                             (str(owner), str(platform))).fetchone()
        if row is None:
            return None
        return self._decode_account(row)

    def _decode_account(self, row):
        if self._fernet is None:
            raise RuntimeError("The configured token encryption key is unavailable or invalid.")
        try:
            secrets = json.loads(self._fernet.decrypt(row["secrets_blob"]).decode("utf-8"))
        except (InvalidToken, ValueError, UnicodeError) as exc:
            raise RuntimeError("Stored provider credentials cannot be decrypted; reconnect the account.") from exc
        return {
            "platform": row["platform"], "secrets": secrets,
            "external_id": row["external_id"] or "", "display_name": row["display_name"] or "",
            "scopes": row["scopes"] or "", "updated_at": row["updated_at"],
        }

    def list_accounts(self, owner):
        with self._db() as db:
            rows = db.execute("SELECT * FROM social_accounts WHERE owner=? ORDER BY platform", (str(owner),)).fetchall()
        accounts = []
        for row in rows:
            try:
                accounts.append(self._decode_account(row))
            except RuntimeError:
                accounts.append({"platform": row["platform"], "secrets": {},
                                 "external_id": row["external_id"] or "",
                                 "display_name": "Reconnect to restore encrypted credentials",
                                 "scopes": "", "updated_at": row["updated_at"],
                                 "unreadable": True})
        return accounts

    def delete_account(self, owner, platform):
        with self._db() as db:
            db.execute("DELETE FROM social_accounts WHERE owner=? AND platform=?", (str(owner), str(platform)))

    def create_upload(self, *, upload_id, owner, platform, render_job_id, source_path, project_id="draft",
                      metadata, settings):
        now = time.time()
        with self._db() as db:
            db.execute("""INSERT INTO social_uploads(id,owner,platform,render_job_id,project_id,source_path,status,
                          phase,progress,message,metadata_json,settings_json,worker_id,created_at,updated_at)
                          VALUES(?,?,?,?,?,?,'queued','queued',0,'Waiting for an upload worker.',?,?,?,?,?)""",
                       (str(upload_id), str(owner), str(platform), str(render_job_id), str(project_id), str(source_path),
                        json.dumps(metadata, ensure_ascii=False), json.dumps(settings, ensure_ascii=False),
                        self.process_id, now, now))

    def latest_upload(self, owner, render_job_id, platform):
        with self._db() as db:
            row = db.execute("""SELECT * FROM social_uploads WHERE owner=? AND render_job_id=? AND platform=?
                              ORDER BY created_at DESC LIMIT 1""",
                             (str(owner), str(render_job_id), str(platform))).fetchone()
        return self._upload_row(row, internal=False) if row else None

    def update_upload(self, upload_id, *, status=None, phase=None, progress=None, message=None,
                      operation_id=None, external_id=None, result_url=None, error=None):
        values, assignments = [], []
        for key, value in (("status", status), ("phase", phase), ("progress", progress),
                           ("message", message), ("external_id", external_id),
                           ("result_url", result_url), ("error", error)):
            if value is not None:
                assignments.append(f"{key}=?")
                values.append(float(value) if key == "progress" else str(value))
        if operation_id is not None:
            encrypted = self._fernet.encrypt(str(operation_id).encode("utf-8")) if self._fernet else None
            assignments.append("operation_blob=?")
            values.append(encrypted)
        assignments.append("updated_at=?")
        values.extend((time.time(), str(upload_id)))
        with self._db() as db:
            db.execute(f"UPDATE social_uploads SET {', '.join(assignments)} WHERE id=?", values)

    def get_upload(self, upload_id, owner, *, internal=False):
        with self._db() as db:
            row = db.execute("SELECT * FROM social_uploads WHERE id=? AND owner=?",
                             (str(upload_id), str(owner))).fetchone()
        return self._upload_row(row, internal=internal) if row else None

    def list_uploads(self, owner, limit=30):
        with self._db() as db:
            rows = db.execute("SELECT * FROM social_uploads WHERE owner=? ORDER BY created_at DESC LIMIT ?",
                              (str(owner), int(limit))).fetchall()
        return [self._upload_row(row, internal=False) for row in rows]

    def _upload_row(self, row, *, internal):
        result = {key: row[key] for key in row.keys()}
        for key in ("metadata_json", "settings_json"):
            try:
                result[key.removesuffix("_json")] = json.loads(result.pop(key))
            except (ValueError, TypeError):
                result[key.removesuffix("_json")] = {}
        blob = result.pop("operation_blob", None)
        if internal:
            if blob and self._fernet:
                try:
                    result["operation_id"] = self._fernet.decrypt(blob).decode("utf-8")
                except (InvalidToken, UnicodeError):
                    result["operation_id"] = None
            else:
                result["operation_id"] = None
            return result
        result.pop("source_path", None)
        result.pop("owner", None)
        result.pop("render_job_id", None)
        return result

"""
db.py — SQLite veritabanı yönetimi.

Tablolar:
  recipients   — Alıcı listesi (ad, email, şirket, grup, aktif, abonelik)
  groups       — Gruplar (VIP, Standart vb.)
  send_log     — Gönderim kaydı (campaign başlığı, alıcı, durum, hata, tarih)

Kullanım:
    db = Database("bulten.db")
    db.init()
"""

import sqlite3
import os
import csv
from datetime import datetime
from typing import List, Dict, Optional


class Database:
    def __init__(self, path: str = "bulten.db"):
        self.path = path
        self._conn: Optional[sqlite3.Connection] = None

    #Bağlantı 

    def connect(self):
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

    # Ayarlar 

    def get_setting(self, key: str, default: str = "") -> str:
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        self.conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value))
        )
        self.conn.commit()

    def get_all_settings(self) -> dict:
        rows = self.conn.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}

    def save_settings(self, data: dict):
        """Birden fazla ayarı tek seferde kaydet."""
        for key, value in data.items():
            self.set_setting(key, value)

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if not self._conn:
            self.connect()
        return self._conn

    def init(self):
        """Tabloları oluştur (yoksa)."""
        self.connect()
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS groups (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT UNIQUE NOT NULL,
                color   TEXT DEFAULT '#1B3A5C'
            );

            INSERT OR IGNORE INTO groups (name, color)
            VALUES ('Standart', '#1B3A5C'), ('VIP', '#e94560');

            CREATE TABLE IF NOT EXISTS recipients (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL DEFAULT '',
                email        TEXT UNIQUE NOT NULL,
                company      TEXT DEFAULT '',
                group_id     INTEGER REFERENCES groups(id) ON DELETE SET NULL,
                active       INTEGER DEFAULT 1,
                subscribed   INTEGER DEFAULT 1,
                unsubscribe_token TEXT,
                created_at   TEXT DEFAULT (datetime('now','localtime')),
                notes        TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS send_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign     TEXT NOT NULL,
                recipient_id INTEGER REFERENCES recipients(id) ON DELETE SET NULL,
                email        TEXT NOT NULL,
                name         TEXT DEFAULT '',
                status       TEXT NOT NULL,   -- 'sent' | 'failed' | 'skipped'
                error_msg    TEXT DEFAULT '',
                sent_at      TEXT DEFAULT (datetime('now','localtime')),
                retried      INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_recipients_email ON recipients(email);
            CREATE INDEX IF NOT EXISTS idx_log_campaign ON send_log(campaign);
            CREATE INDEX IF NOT EXISTS idx_log_status ON send_log(status);

            CREATE TABLE IF NOT EXISTS campaigns (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL DEFAULT '',
                subject    TEXT NOT NULL DEFAULT '',
                blocks     TEXT NOT NULL DEFAULT '[]',
                settings   TEXT NOT NULL DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            );
        """)
        self.conn.commit()

    #Grup işlemleri

    def get_groups(self) -> List[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM groups ORDER BY name"
        ).fetchall()

    def add_group(self, name: str, color: str = "#1B3A5C") -> int:
        cur = self.conn.execute(
            "INSERT INTO groups (name, color) VALUES (?, ?)", (name, color)
        )
        self.conn.commit()
        return cur.lastrowid

    def update_group(self, group_id: int, name: str, color: str):
        self.conn.execute(
            "UPDATE groups SET name=?, color=? WHERE id=?", (name, color, group_id)
        )
        self.conn.commit()

    def delete_group(self, group_id: int):
        self.conn.execute("DELETE FROM groups WHERE id=?", (group_id,))
        self.conn.commit()

    #Alıcı işlemleri

    def get_recipients(self, group_id: Optional[int] = None,
                       active_only: bool = True,
                       subscribed_only: bool = True) -> List[sqlite3.Row]:
        query = """
            SELECT r.*, g.name as group_name, g.color as group_color
            FROM recipients r
            LEFT JOIN groups g ON r.group_id = g.id
            WHERE 1=1
        """
        params = []
        if active_only:
            query += " AND r.active=1"
        if subscribed_only:
            query += " AND r.subscribed=1"
        if group_id is not None:
            query += " AND r.group_id=?"
            params.append(group_id)
        query += " ORDER BY r.name COLLATE NOCASE"
        return self.conn.execute(query, params).fetchall()

    def get_recipient_count(self, group_id: Optional[int] = None,
                            active_only=True, subscribed_only=True) -> int:
        rows = self.get_recipients(group_id, active_only, subscribed_only)
        return len(rows)

    def add_recipient(self, name: str, email: str, company: str = "",
                      group_id: Optional[int] = None, notes: str = "") -> int:
        import secrets
        token = secrets.token_urlsafe(16)
        cur = self.conn.execute(
            """INSERT INTO recipients (name, email, company, group_id, notes, unsubscribe_token)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name.strip(), email.strip().lower(), company.strip(), group_id, notes, token)
        )
        self.conn.commit()
        return cur.lastrowid

    def update_recipient(self, rid: int, name: str, email: str,
                         company: str, group_id: Optional[int],
                         notes: str = "", active: int = 1, subscribed: int = 1):
        self.conn.execute(
            """UPDATE recipients
               SET name=?, email=?, company=?, group_id=?, notes=?, active=?, subscribed=?
               WHERE id=?""",
            (name.strip(), email.strip().lower(), company.strip(),
             group_id, notes, active, subscribed, rid)
        )
        self.conn.commit()

    def delete_recipient(self, rid: int):
        self.conn.execute("UPDATE recipients SET active=0 WHERE id=?", (rid,))
        self.conn.commit()

    def unsubscribe(self, rid: int):
        self.conn.execute(
            "UPDATE recipients SET subscribed=0 WHERE id=?", (rid,)
        )
        self.conn.commit()

    def resubscribe(self, rid: int):
        self.conn.execute(
            "UPDATE recipients SET subscribed=1, active=1 WHERE id=?", (rid,)
        )
        self.conn.commit()

    def import_csv(self, filepath: str,
                   default_group_id: Optional[int] = None) -> Dict:
        """CSV içe aktar. Sütun adları: name/ad, email/mail, company/sirket, group/grup"""
        added = skipped = errors = 0
        error_list = []
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                keys = {k.lower().strip(): v for k, v in row.items()}
                email = (keys.get('email') or keys.get('mail') or '').strip().lower()
                name  = (keys.get('name') or keys.get('ad') or keys.get('isim') or '').strip()
                company = (keys.get('company') or keys.get('sirket') or
                           keys.get('şirket') or '').strip()
                if not email or '@' not in email:
                    errors += 1
                    error_list.append(f"Satır {i}: geçersiz email — {email!r}")
                    continue
                try:
                    self.add_recipient(name, email, company, default_group_id)
                    added += 1
                except sqlite3.IntegrityError:
                    skipped += 1
        return {"added": added, "skipped": skipped,
                "errors": errors, "error_list": error_list}

    # Gönderim logu

    def log_send(self, campaign: str, recipient_id: Optional[int],
                 email: str, name: str, status: str,
                 error_msg: str = "", retried: int = 0):
        self.conn.execute(
            """INSERT INTO send_log
               (campaign, recipient_id, email, name, status, error_msg, retried)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (campaign, recipient_id, email, name, status, error_msg, retried)
        )
        self.conn.commit()

    def get_logs(self, campaign: Optional[str] = None,
                 status: Optional[str] = None,
                 limit: int = 500) -> List[sqlite3.Row]:
        query = "SELECT * FROM send_log WHERE 1=1"
        params = []
        if campaign:
            query += " AND campaign=?"
            params.append(campaign)
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY sent_at DESC LIMIT ?"
        params.append(limit)
        return self.conn.execute(query, params).fetchall()

    def get_campaigns(self) -> List[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT campaign FROM send_log ORDER BY campaign"
        ).fetchall()
        return [r["campaign"] for r in rows]

    def get_log_summary(self, campaign: str) -> Dict:
        rows = self.conn.execute(
            """SELECT status, COUNT(*) as cnt
               FROM send_log WHERE campaign=?
               GROUP BY status""", (campaign,)
        ).fetchall()
        return {r["status"]: r["cnt"] for r in rows}

    def get_failed_for_campaign(self, campaign: str) -> List[sqlite3.Row]:
        return self.conn.execute(
            """SELECT sl.*, r.id as rid
               FROM send_log sl
               LEFT JOIN recipients r ON sl.recipient_id = r.id
               WHERE sl.campaign=? AND sl.status='failed'""",
            (campaign,)
        ).fetchall()

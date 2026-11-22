"""Excel tracker: one row per test user ever created."""
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

COLUMNS = ["created_at", "name", "user_id", "email", "password", "login_url", "status"]


class Tracker:
    def __init__(self, path):
        self.path = Path(path)
        if self.path.exists():
            self.wb = load_workbook(self.path)
            self.ws = self.wb.active
        else:
            self.wb = Workbook()
            self.ws = self.wb.active
            self.ws.title = "test_users"
            self.ws.append(COLUMNS)
            for cell in self.ws[1]:
                cell.font = Font(bold=True)
            self.ws.freeze_panes = "A2"
            for letter, width in zip("ABCDEFG", (22, 24, 20, 40, 18, 60, 10)):
                self.ws.column_dimensions[letter].width = width

    def rows(self):
        return [
            dict(zip(COLUMNS, row))
            for row in self.ws.iter_rows(min_row=2, values_only=True)
            if any(row)
        ]

    def names(self):
        return {r["name"] for r in self.rows()}

    def add(self, name, user):
        self.ws.append([
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            name,
            str(user.get("id", "")),
            user.get("email", ""),
            user.get("password", ""),
            user.get("login_url", ""),
            "active",
        ])

    def mark_deleted(self, user_id):
        col = COLUMNS.index("user_id")
        for row in self.ws.iter_rows(min_row=2):
            if str(row[col].value) == str(user_id):
                row[COLUMNS.index("status")].value = "deleted"

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.wb.save(self.path)

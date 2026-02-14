#!/usr/bin/env python3
"""
Google Sheets Reader for Bulk Quotes Image Generator
Fetches quotes data from Google Sheets Database worksheet
Updated to use correct sheet URL and Database worksheet
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

class SheetReader:
    def __init__(self, credentials_path="credentials.json"):
        """Initialize with Google credentials"""
        self.credentials_path = credentials_path
        self.client = None
        self.spreadsheet = None
        self.cache = {}
        self.config = self._load_config()
        
        # Use the correct sheet URL
        self.sheet_url = "https://docs.google.com/spreadsheets/d/1jn1DroWU8GB5Sc1rQ7wT-WusXK9v4V05ISYHgUEjYZc/edit"

    def _load_config(self) -> dict:
        try:
            config_path = Path("references") / "config.json"
            if config_path.exists():
                return json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _get_database_worksheet_name(self) -> str:
        return "Database"  # Fixed to use the correct worksheet name

    def _col_to_index(self, col: Any, default_idx: int) -> int:
        if isinstance(col, int):
            return col
        col_str = str(col or "").strip().upper()
        col_idx = 0
        for ch in col_str:
            if not ('A' <= ch <= 'Z'):
                continue
            col_idx = col_idx * 26 + (ord(ch) - ord('A') + 1)
        return col_idx if col_idx > 0 else default_idx

    def connect(self, sheet_url=None):
        """Connect to Google Sheets"""
        try:
            # Get credentials with both Sheets and Drive scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=scopes
            )
            self.client = gspread.authorize(creds)

            # Open spreadsheet using the correct URL
            url_to_use = sheet_url or self.sheet_url
            self.spreadsheet = self.client.open_by_url(url_to_use)
            
            return True
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            return False

    def get_topics(self):
        """Get list of all available topics from CATEGORY column"""
        if not self.spreadsheet:
            return []
        
        try:
            worksheet = self.spreadsheet.worksheet(self._get_database_worksheet_name())
            records = worksheet.get_all_records()

            def _get_any(d: dict, *keys: str, default: Any = None) -> Any:
                for k in keys:
                    if k in d and d.get(k) not in (None, ""):
                        return d.get(k)
                return default

            sheet_cfg = self.config.get("google_sheets") or {}
            done_value = str(sheet_cfg.get("status_done_value", "Done")).strip().lower()

            topics = set()
            for record in records:
                status_val = _get_any(record, 'STATUS', 'Status', 'status', default='')
                if str(status_val).strip().lower() == done_value:
                    continue
                cat = _get_any(record, 'CATEGORY', 'Category', 'Category ', 'category', default='')
                cat = str(cat).strip()
                if cat:
                    topics.add(cat)

            return sorted(topics)
        except Exception as e:
            print(f"Error fetching topics: {e}")
            return []

    def get_all_topics(self):
        """Backward-compatible alias used by scripts/dashboard.py"""
        return self.get_topics()

    def get_quotes(self, topic):
        """Get all quotes for a specific topic from CATEGORY column"""
        if not self.spreadsheet:
            return []
        
        # Check cache first
        if topic in self.cache:
            return self.cache[topic]

        try:
            worksheet = self.spreadsheet.worksheet(self._get_database_worksheet_name())
            records = worksheet.get_all_records()
             
            def _get_any(d: dict, *keys: str, default: Any = None) -> Any:
                for k in keys:
                    if k in d and d.get(k) not in (None, ""):
                        return d.get(k)
                return default

            sheet_cfg = self.config.get("google_sheets") or {}
            max_len = sheet_cfg.get("max_length")
            english_only = bool(sheet_cfg.get("english_only"))
            done_value = str(sheet_cfg.get("status_done_value", "Done")).strip().lower()
            skip_value = str(sheet_cfg.get("status_skip_value", "Skip")).strip()

            def _is_english(s: str) -> bool:
                try:
                    s.encode("ascii")
                    return True
                except Exception:
                    return False

            quotes = []
            for idx, record in enumerate(records, start=2):
                status_val = _get_any(record, 'STATUS', 'Status', 'status', default='')
                if str(status_val).strip().lower() == done_value:
                    continue

                cat = _get_any(record, 'CATEGORY', 'Category', 'Category ', 'category', default='')
                if str(cat).strip() != str(topic).strip():
                    continue

                length_val = _get_any(record, 'LENGTH', 'Length', 'length', default=None)
                try:
                    length_num = int(length_val) if length_val not in (None, "") else None
                except Exception:
                    length_num = None
                if isinstance(max_len, int) and length_num is not None and length_num > max_len:
                    continue

                quote_text = _get_any(record, 'QUOTE', 'Quote', 'quote', default='')
                if quote_text:
                    if english_only and not _is_english(str(quote_text)):
                        continue
                    quotes.append({
                        'quote': quote_text,
                        'translate': _get_any(record, 'TRANSLATE', 'Translate', 'translate', default=''),
                        'author': _get_any(record, 'AUTHOR', 'Author', 'author', default='Unknown'),
                        'category': _get_any(record, 'CATEGORY', 'Category', 'Category ', 'category', default=topic),
                        'tags': _get_any(record, 'TAGS', 'Tags', 'tags', default=''),
                        'image': _get_any(record, 'IMAGE', 'Image', 'image', default=''),
                        'author_image': _get_any(record, 'IMAGE', 'Image', 'image', default=''),
                        'length': length_num,
                        '_row': idx,
                    })
            
            # Cache the results
            self.cache[topic] = quotes
            return quotes
            
        except Exception as e:
            print(f"Error fetching quotes for {topic}: {e}")
            return []

    def get_quotes_by_topic(self, topic: str):
        """Backward-compatible alias used by scripts/dashboard.py"""
        return self.get_quotes(topic)

    def get_remaining_quotes(self, topic):
        """Return remaining (not Done) counts for the given topic"""
        if not self.spreadsheet:
            return {"topic_total": 0, "authors": {}}

        try:
            worksheet = self.spreadsheet.worksheet(self._get_database_worksheet_name())
            records = worksheet.get_all_records()

            def _get_any(d: dict, *keys: str, default: Any = None) -> Any:
                for k in keys:
                    if k in d and d.get(k) not in (None, ""):
                        return d.get(k)
                return default

            sheet_cfg = self.config.get("google_sheets") or {}
            done_value = str(sheet_cfg.get("status_done_value", "Done")).strip().lower()
            max_len = sheet_cfg.get("max_length")
            english_only = bool(sheet_cfg.get("english_only"))

            def _is_english(s: str) -> bool:
                try:
                    s.encode("ascii")
                    return True
                except Exception:
                    return False

            topic_total = 0
            authors: dict[str, int] = {}
            for record in records:
                status_val = _get_any(record, 'STATUS', 'Status', 'status', default='')
                if str(status_val).strip().lower() == done_value:
                    continue

                cat = _get_any(record, 'CATEGORY', 'Category', 'Category ', 'category', default='')
                if str(cat).strip() != str(topic).strip():
                    continue

                length_val = _get_any(record, 'LENGTH', 'Length', 'length', default=None)
                try:
                    length_num = int(length_val) if length_val not in (None, "") else None
                except Exception:
                    length_num = None
                if isinstance(max_len, int) and length_num is not None and length_num > max_len:
                    continue

                quote_text = _get_any(record, 'QUOTE', 'Quote', 'quote', default='')
                if not quote_text:
                    continue
                if english_only and not _is_english(str(quote_text)):
                    continue

                a = _get_any(record, 'AUTHOR', 'Author', 'author', default='Unknown')
                a = str(a).strip() or 'Unknown'

                topic_total += 1
                authors[a] = int(authors.get(a, 0)) + 1

            return {"topic_total": int(topic_total), "authors": authors}
        except Exception as e:
            print(f"Error computing remaining counts: {e}")
            return {"topic_total": 0, "authors": {}}

    def get_remaining_counts(self, topic: str) -> dict:
        """Backward-compatible alias used by scripts/dashboard.py"""
        return self.get_remaining_quotes(topic)

    def mark_as_generated(self, topic: str, row: int, image_path: str) -> str:
        """Mark quote as generated and update sheet"""
        if not self.spreadsheet:
            return "Failed: No spreadsheet connection"

        try:
            worksheet = self.spreadsheet.worksheet(self._get_database_worksheet_name())

            worksheet.update_cell(int(row), 11, f'=HYPERLINK("{image_path}","Preview Image")')
            worksheet.update_cell(int(row), 12, "Done")
            worksheet.update_cell(int(row), 13, "1080x1080")
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            worksheet.update_cell(int(row), 14, ts)

            return f"Successfully updated row {row}"
        except Exception as e:
            return f"Error updating sheet: {e}"

    def write_back(self, topic: str, row: int, image_url: str) -> bool:
        """Write preview link + mark Done (compat for dashboard)."""
        res = self.mark_as_generated(topic=topic, row=row, image_path=image_url)
        return str(res).lower().startswith("successfully")

    def write_generation_meta(self, row: int, dimensions: str, timestamp: str) -> bool:
        """Write DIMENSIONS + GENERATED_AT (compat for dashboard)."""
        if not self.spreadsheet:
            return False
        try:
            worksheet = self.spreadsheet.worksheet(self._get_database_worksheet_name())
            if dimensions is not None:
                worksheet.update_cell(int(row), 13, str(dimensions))
            if timestamp is not None:
                worksheet.update_cell(int(row), 14, str(timestamp))
            return True
        except Exception as e:
            print(f"Error writing generation meta: {e}")
            return False

# Standalone function for easy import
def fetch_quotes(topic, credentials_path="credentials.json"):
    """Quick function to fetch quotes"""
    reader = SheetReader(credentials_path)
    if reader.connect():
        return reader.get_quotes(topic)
    return []
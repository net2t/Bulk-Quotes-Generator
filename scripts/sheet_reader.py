#!/usr/bin/env python3
"""
Google Sheets Reader
Fetches quotes data from Google Sheets
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

    def _load_config(self) -> dict:
        try:
            config_path = Path("references") / "config.json"
            if config_path.exists():
                return json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _get_sheet_url(self) -> Optional[str]:
        sheet_url = os.getenv("GOODREADS_SHEET_URL")
        if sheet_url:
            return sheet_url
        return (self.config.get("google_sheets") or {}).get("sheet_url")

    def _get_database_worksheet_name(self) -> str:
        sheet_cfg = self.config.get("google_sheets") or {}
        return str(sheet_cfg.get("database_worksheet", "Database"))

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
            # Get credentials
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=scopes
            )
            self.client = gspread.authorize(creds)

            # Open spreadsheet
            if sheet_url:
                self.spreadsheet = self.client.open_by_url(sheet_url)
            else:
                # Try to get from environment or config
                sheet_url = self._get_sheet_url()
                if sheet_url:
                    self.spreadsheet = self.client.open_by_url(sheet_url)
                else:
                    raise ValueError("Sheet URL not provided")
            
            return True
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            return False

    def get_all_topics(self):
        """Get list of all available topics (unique CATEGORY values)"""
        if not self.spreadsheet:
            return []
        
        try:
            ws_name = self._get_database_worksheet_name()
            worksheet = self.spreadsheet.worksheet(ws_name)
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

    def write_back(self, topic: str, row: int, value: str) -> bool:
        """Write back generated image link/path to a configured sheet column (Database sheet)"""
        if not self.spreadsheet:
            return False

        sheet_cfg = self.config.get("google_sheets") or {}
        col = sheet_cfg.get("write_back_column", "H")
        status_col = sheet_cfg.get("status_column", "I")
        done_value = sheet_cfg.get("status_done_value", "Done")

        try:
            worksheet = self.spreadsheet.worksheet(self._get_database_worksheet_name())
            col_idx = self._col_to_index(col, 8)
 
            cell_value = value
            if isinstance(value, str) and value.strip().lower().startswith('http'):
                url = value.replace('"', "'")
                cell_value = f'=HYPERLINK("{url}","Preview Image")'
            worksheet.update_cell(int(row), int(col_idx), cell_value)

            # Mark Done
            status_idx = self._col_to_index(status_col, 9)
            worksheet.update_cell(int(row), int(status_idx), str(done_value))
            return True
        except Exception as e:
            print(f"Error writing back to sheet: {e}")
            return False

    def write_generation_meta(self, row: int, dimensions: str, generated_at: str) -> bool:
        """Write generation metadata (dimensions + timestamp) to the end of the Database sheet.

        Creates the columns if headers do not exist.
        """
        if not self.spreadsheet:
            return False

        try:
            worksheet = self.spreadsheet.worksheet(self._get_database_worksheet_name())
            headers = worksheet.row_values(1)
            headers_norm = [str(h or '').strip() for h in headers]

            def _ensure_header(name: str) -> int:
                for i, h in enumerate(headers_norm, start=1):
                    if h.strip().lower() == name.strip().lower():
                        return i
                idx = len(headers_norm) + 1
                worksheet.update_cell(1, idx, name)
                headers_norm.append(name)
                return idx

            dim_idx = _ensure_header('DIMENSIONS')
            ts_idx = _ensure_header('GENERATED_AT')

            worksheet.update_cell(int(row), int(dim_idx), str(dimensions))
            worksheet.update_cell(int(row), int(ts_idx), str(generated_at))
            return True
        except Exception as e:
            print(f"Error writing generation meta: {e}")
            return False

    def write_status(self, topic: str, row: int, status: str) -> bool:
        """Write a status value to the configured status column (Database sheet)"""
        if not self.spreadsheet:
            return False

        sheet_cfg = self.config.get("google_sheets") or {}
        status_col = sheet_cfg.get("status_column", "I")
        try:
            worksheet = self.spreadsheet.worksheet(self._get_database_worksheet_name())
            status_idx = self._col_to_index(status_col, 9)
            worksheet.update_cell(int(row), int(status_idx), str(status))
            return True
        except Exception as e:
            print(f"Error writing status to sheet: {e}")
            return False

    def get_quotes_by_topic(self, topic):
        """Get all quotes for a specific topic (CATEGORY filter in Database sheet)"""
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
                # Heuristic: allow common punctuation and ASCII only.
                # Keeps dashboard bounded to English-ish text without extra deps.
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
                    # Mark Skip (does not meet requirement)
                    self.write_status(topic, idx, skip_value)
                    continue

                quote_text = _get_any(record, 'QUOTE', 'Quote', 'quote', default='')
                if quote_text:
                    if english_only and not _is_english(str(quote_text)):
                        self.write_status(topic, idx, skip_value)
                        continue
                    quotes.append({
                        'quote': quote_text,
                        'author': _get_any(record, 'AUTHOR', 'Author', 'author', 'POET', 'Poet', 'poet', default='Unknown'),
                        'category': _get_any(record, 'CATEGORY', 'Category', 'Category ', 'category', default=topic),
                        'tags': _get_any(record, 'TAGS', 'Tags', 'tags', default=''),
                        'likes': _get_any(record, 'LIKES', 'Likes', 'likes', default=0),
                        'image': _get_any(record, 'IMAGE', 'Image', 'image', default=''),
                        'author_image': _get_any(
                            record,
                            'AUTHOR_IMAGE', 'Author Image', 'author_image',
                            'AVATAR', 'Avatar', 'avatar',
                            'PHOTO', 'Photo', 'photo',
                            'IMAGE_URL', 'Image URL', 'image_url',
                            'IMAGE', 'Image', 'image',
                            default=''
                        ),
                        'length': length_num,
                        '_row': idx,
                    })
            
            # Cache the results
            self.cache[topic] = quotes
            return quotes
            
        except Exception as e:
            print(f"Error fetching quotes for {topic}: {e}")
            return []
    
    def get_random_quote(self, topic):
        """Get a random quote from a topic"""
        import random
        quotes = self.get_quotes_by_topic(topic)
        if quotes:
            return random.choice(quotes)
        return None

# Standalone function for easy import
def fetch_quotes(topic, credentials_path="credentials.json", sheet_url=None):
    """Quick function to fetch quotes"""
    reader = SheetReader(credentials_path)
    if reader.connect(sheet_url):
        return reader.get_quotes_by_topic(topic)
    return []

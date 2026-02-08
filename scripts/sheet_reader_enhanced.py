#!/usr/bin/env python3
"""
Enhanced Google Sheets Reader
Fetches quotes data from Google Sheets with AI prompt auto-generation
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import json
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime

# Import AI prompt generator
try:
    from ai_prompt_generator import AIPromptGenerator
    AI_AVAILABLE = True
except ImportError:
    AIPromptGenerator = None
    AI_AVAILABLE = False
    print("⚠️  AI Prompt Generator not available")


class EnhancedSheetReader:
    """Enhanced Sheet Reader with AI prompt auto-generation"""
    
    def __init__(self, credentials_path="credentials.json"):
        """Initialize with Google credentials"""
        self.credentials_path = credentials_path
        self.client = None
        self.spreadsheet = None
        self.cache = {}
        self.config = self._load_config()
        
        # Initialize AI prompt generator if available
        self.ai_generator = AIPromptGenerator() if AI_AVAILABLE else None
        
        # Track which columns exist
        self.columns = {}
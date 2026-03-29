import os
import json
from pathlib import Path

class JsonManager:
    def __init__(self, file: str):
        self.file = file
        self.data = {}
        self.base_dir = Path(__file__).parent
        self.load_files()

    def load_files(self):
        file_path = self.base_dir / self.file
        if file_path.exists():
            with open(file_path, mode="r", encoding="utf-8") as f:
                content = f.read()
                file_data = json.loads(content)
                self.data.update(file_data)

    def get_value(self, key: str):
        value = self.data.get(key)
        if value is None:
            raise ValueError(f"Cannot access to phrase variable: {key}")
        return value

BOT_TOKEN = os.getenv("BOT_TOKEN", None)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)

if BOT_TOKEN is None or GOOGLE_API_KEY is None:
    raise Exception("Necessary environment variable not set")

phrases = JsonManager("phrases.json")

THINKING_BUDGET = 4096

ALLOWED_USERS = [int(i.strip()) for i in os.getenv("ALLOWED_USERS", "").split(",") if i.strip().isdigit()]
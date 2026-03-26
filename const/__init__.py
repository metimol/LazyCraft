import os
import json
import asyncio
import aiofiles
from pathlib import Path


class AsyncJsonManager:
    def __init__(self, file: str):
        self.file = file
        self.data = {}
        self.base_dir = Path(__file__).parent

    async def load_files(self):
        await asyncio.gather(
            self._load_file(self.file),
        )

    async def _load_file(self, filename: str):
        file_path = self.base_dir / filename
        if file_path.exists():
            async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
                content = await f.read()
                file_data = json.loads(content)
                self.data.update(file_data)

    def get_value(self, key: str):
        return self.data.get(key, key)


BOT_TOKEN = os.getenv("BOT_TOKEN", None)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)

if BOT_TOKEN is None or GOOGLE_API_KEY is None:
    raise Exception("Necessary environment variable not set")

phrases = AsyncJsonManager("phrases.json")

THINKING_BUDGET = 4096
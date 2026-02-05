"""
Configuration management for the listing monitor.
Loads settings from environment variables or .env file.
"""

import os
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class Config:
    """Application configuration loaded from environment variables."""

    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')

    # Fanatics Collect credentials
    FANATICS_EMAIL: str = os.getenv('FANATICS_EMAIL', '')
    FANATICS_PASSWORD: str = os.getenv('FANATICS_PASSWORD', '')

    # Search settings
    SEARCH_TERM: str = os.getenv('SEARCH_TERM', '1996 no rarity')

    # Pokemon filter - only alert for listings containing these Pokemon names
    # Includes both English and Japanese names for Mercari Japan support
    TARGET_POKEMON: list[str] = [
        # Holos (English + Japanese)
        'alakazam', 'フーディン',
        'gyarados', 'ギャラドス',
        'charizard', 'リザードン',
        'blastoise', 'カメックス',
        'venusaur', 'フシギバナ',
        'chansey', 'ラッキー',
        'clefairy', 'ピッピ',
        'hitmonchan', 'エビワラー',
        'machamp', 'カイリキー',
        'magneton', 'レアコイル',
        'mewtwo', 'ミュウツー',
        'nidoking', 'ニドキング',
        'ninetales', 'キュウコン',
        'poliwrath', 'ニョロボン',
        'raichu', 'ライチュウ',
        'zapdos', 'サンダー',
        # Starters (all evolutions)
        'bulbasaur', 'フシギダネ',
        'ivysaur', 'フシギソウ',
        'charmander', 'ヒトカゲ',
        'charmeleon', 'リザード',
        'squirtle', 'ゼニガメ',
        'wartortle', 'カメール',
        # Special
        'pikachu', 'ピカチュウ',
        'magikarp', 'コイキング',
        'electrode', 'マルマイン',
        'electabuzz', 'エレブー',
        # Dragon line
        'dratini', 'ミニリュウ',
        'dragonair', 'ハクリュー',
    ]

    # File paths
    BASE_DIR: Path = Path(__file__).parent
    DATA_DIR: Path = BASE_DIR / 'data'
    SEEN_LISTINGS_FILE: Path = DATA_DIR / 'seen_listings.json'
    LOG_FILE: Path = DATA_DIR / 'monitor.log'

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration. Returns list of missing items."""
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
        if not cls.TELEGRAM_CHAT_ID:
            missing.append('TELEGRAM_CHAT_ID')
        return missing

    @classmethod
    def is_telegram_configured(cls) -> bool:
        """Check if Telegram is properly configured."""
        return bool(cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID)

    @classmethod
    def is_fanatics_configured(cls) -> bool:
        """Check if Fanatics credentials are configured."""
        return bool(cls.FANATICS_EMAIL and cls.FANATICS_PASSWORD)


# Ensure data directory exists
Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

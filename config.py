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
    WSJ_TELEGRAM_BOT_TOKEN: str = os.getenv('WSJ_TELEGRAM_BOT_TOKEN', '')
    WSJ_TELEGRAM_CHAT_ID: str = os.getenv('WSJ_TELEGRAM_CHAT_ID', '')

    # Monitored searches — each has a keyword, platform, and title validators
    # validators: list of lists — each inner list = alternatives (OR), all outer lists must pass (AND)
    MONITORED_SEARCHES: list[dict] = [
        {
            'name': 'Naruto Vol 1 First Edition',
            'platform': 'mercari',
            'keyword': 'naruto 1巻 初版',
            'state_category': 'mercari_naruto_v1',
            'validators': [['ナルト', 'naruto'], ['1巻']],
        },
        {
            'name': 'CoroCoro Comic Nov 1996',
            'platform': 'mercari',
            'keyword': 'コロコロコミック 1996年 11月号',
            'state_category': 'mercari_corocoro_nov96',
            'validators': [['コロコロ', 'corocoro'], ['1996'], ['11']],
        },
        {
            'name': 'WSJ 1996 #41 Romance Dawn',
            'platform': 'mercari',
            'keyword': '週刊少年ジャンプ 1996 41 ロマンスドーン',
            'state_category': 'mercari_wsj_41_romancedawn',
            'validators': [['ジャンプ', 'jump'], ['1996'], ['41']],
        },
        {
            'name': 'WSJ 1996 No 41',
            'platform': 'ebay',
            'keyword': 'weekly shonen jump 1996 no 41',
            'state_category': 'ebay_wsj_1996_41',
            'validators': [['jump'], ['1996'], ['41']],
        },
        {
            'name': 'WSJ 1997 Vol 34',
            'platform': 'ebay',
            'keyword': 'weekly shonen jump 1997 vol 34',
            'state_category': 'ebay_wsj_1997_34',
            'validators': [['jump'], ['1997'], ['34']],
        },
        {
            'name': 'Pokemon Red 22 (eBay)',
            'platform': 'ebay',
            'keyword': 'pokemon red gameboy 22',
            'state_category': 'ebay_pokemon_red_1st',
            'bot': 'wsj',
            'validators': [
                ['pokemon', 'ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['red', '赤', 'レッド'],
                ['gameboy', 'game boy'],
                ['22'],
            ],
        },
        {
            'name': 'Pokemon Green 00 (eBay)',
            'platform': 'ebay',
            'keyword': 'pokemon green gameboy 00',
            'state_category': 'ebay_pokemon_green_1st',
            'bot': 'wsj',
            'validators': [
                ['pokemon', 'ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['green', '緑', 'グリーン'],
                ['gameboy', 'game boy'],
                ['00'],
            ],
        },
        {
            'name': 'Pokemon Green 1996 初版 (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター 初版 00',
            'state_category': 'mercari_pokemon_green_1st',
            'bot': 'wsj',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pokemon', 'pocket monster'],
                ['初版', 'first edition', '1st'],
                ['00', '緑', 'グリーン', 'green'],
            ],
        },
        {
            'name': 'Pokemon Red 1996 初版 (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター 初版 22',
            'state_category': 'mercari_pokemon_red_1st',
            'bot': 'wsj',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pokemon', 'pocket monster'],
                ['初版', 'first edition', '1st'],
                ['22', '赤', 'レッド', 'red'],
            ],
        },
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


# Ensure data directory exists
Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

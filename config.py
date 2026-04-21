"""
Configuration for the No-Rarity Scanner (Pokemon game cartridge monitor).
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

    # Telegram settings (main bot for Pokemon scanner)
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')
    WSJ_TELEGRAM_BOT_TOKEN: str = os.getenv('WSJ_TELEGRAM_BOT_TOKEN', '')
    WSJ_TELEGRAM_CHAT_ID: str = os.getenv('WSJ_TELEGRAM_CHAT_ID', '')

    # Global exclude terms — reject any listing whose title contains these (reprint indicators)
    GLOBAL_EXCLUDE: list[str] = [
        'reprint', 'reproduction',
        '再版', '重版', '復刻', '復刻版', '再刷', '複製',
    ]

    # Monitored searches — Pokemon game cartridges only
    # validators: list of lists — each inner list = alternatives (OR), all outer lists must pass (AND)
    # optional 'exclude': per-search extra exclude terms (on top of GLOBAL_EXCLUDE)
    MONITORED_SEARCHES: list[dict] = [
        {
            'name': 'Pokemon Red Early Cart (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター 赤 初期 ゲームボーイ',
            'state_category': 'mercari_pokemon_red_1st',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['赤', 'レッド', 'red', 'aka'],
                ['22', '00', '初期'],
                ['ゲームボーイ', 'gameboy', 'game boy', 'gb', '刻印'],
            ],
        },
        {
            'name': 'Pokemon Red Early Cart (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ポケットモンスター 赤 初期 ゲームボーイ',
            'state_category': 'yahoo_pokemon_red_1st',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['赤', 'レッド', 'red', 'aka'],
                ['22', '00', '初期'],
                ['ゲームボーイ', 'gameboy', 'game boy', 'gb', '刻印'],
            ],
        },
        {
            'name': 'Pokemon Green Early Cart (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター 緑 初期 ゲームボーイ',
            'state_category': 'mercari_pokemon_green_1st',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['緑', 'グリーン', 'green', 'midori'],
                ['22', '00', '初期'],
                ['ゲームボーイ', 'gameboy', 'game boy', 'gb', '刻印'],
            ],
        },
        {
            'name': 'Pokemon Green Early Cart (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ポケットモンスター 緑 初期 ゲームボーイ',
            'state_category': 'yahoo_pokemon_green_1st',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['緑', 'グリーン', 'green', 'midori'],
                ['22', '00', '初期'],
                ['ゲームボーイ', 'gameboy', 'game boy', 'gb', '刻印'],
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

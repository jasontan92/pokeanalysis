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

    # Global exclude terms — reject any listing whose title contains these (reprint indicators)
    GLOBAL_EXCLUDE: list[str] = [
        'reprint', 'reproduction',
        '再版', '重版', '復刻', '復刻版', '再刷', '複製',
    ]

    # Monitored searches — each has a keyword, platform, and title validators
    # validators: list of lists — each inner list = alternatives (OR), all outer lists must pass (AND)
    # optional 'exclude': per-search extra exclude terms (on top of GLOBAL_EXCLUDE)
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
        # JoJo's Bizarre Adventure - WSJ 1987 #1-2
        {
            'name': 'WSJ 1987 #1-2 JoJo',
            'platform': 'mercari',
            'keyword': '週刊少年ジャンプ 1987 1・2 ジョジョ',
            'state_category': 'mercari_wsj_jojo',
            'validators': [['ジャンプ', 'jump'], ['1987'], ['ジョジョ', 'jojo']],
        },
        {
            'name': 'WSJ 1987 JoJo',
            'platform': 'ebay',
            'keyword': 'weekly shonen jump 1987 jojo',
            'state_category': 'ebay_wsj_jojo',
            'validators': [['jump'], ['1987'], ['jojo']],
        },
        # Hunter x Hunter - WSJ 1998 #14
        {
            'name': 'WSJ 1998 #14 HxH',
            'platform': 'mercari',
            'keyword': '週刊少年ジャンプ 1998 14 ハンターハンター',
            'state_category': 'mercari_wsj_hxh',
            'validators': [['ジャンプ', 'jump'], ['1998'], ['14']],
        },
        {
            'name': 'WSJ 1998 No 14 HxH',
            'platform': 'ebay',
            'keyword': 'weekly shonen jump 1998 no 14 hunter',
            'state_category': 'ebay_wsj_hxh',
            'validators': [['jump'], ['1998'], ['14']],
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
            'keyword': 'ポケットモンスター 緑 初版 ゲームボーイ',
            'state_category': 'mercari_pokemon_green_1st',
            'bot': 'wsj',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['初版', '初期版', '初期'],
                ['ゲームボーイ', 'gameboy', 'game boy', 'gb', '刻印'],
                ['00', '緑', 'グリーン', 'green', 'midori'],
            ],
        },
        {
            'name': 'Pokemon Green 刻印 (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター 緑 刻印 00',
            'state_category': 'mercari_pokemon_green_1st',
            'bot': 'wsj',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['緑', 'グリーン', 'green'],
                ['00'],
            ],
        },
        {
            'name': 'Pokemon Red 1996 初版 (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター 赤 初版 ゲームボーイ',
            'state_category': 'mercari_pokemon_red_1st',
            'bot': 'wsj',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['初版', '初期版', '初期'],
                ['ゲームボーイ', 'gameboy', 'game boy', 'gb', '刻印'],
                ['22', '赤', 'レッド', 'red', 'aka'],
            ],
        },
        {
            'name': 'Pokemon Red 刻印 (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター 赤 刻印 22',
            'state_category': 'mercari_pokemon_red_1st',
            'bot': 'wsj',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['赤', 'レッド', 'red'],
                ['22'],
            ],
        },
        {
            'name': 'Yu-Gi-Oh Vol 1 初版 (Mercari)',
            'platform': 'mercari',
            'keyword': '遊戯王 1巻 初版',
            'state_category': 'mercari_yugioh_v1_1st',
            'validators': [
                ['遊戯王', 'yugioh', 'yu-gi-oh'],
                ['1巻'],
                ['初版', '第1刷', '第一刷'],
            ],
        },
        {
            'name': 'One Piece Vol 1 初版 (Mercari)',
            'platform': 'mercari',
            'keyword': 'ワンピース 1巻 初版 第1刷',
            'state_category': 'mercari_onepiece_v1_1st',
            'validators': [
                ['ワンピース', 'onepiece', 'one piece'],
                ['1巻'],
                ['初版', '第1刷', '第一刷'],
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

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
        # --- Satoshi Tajiri "New Game Design" book (Pokemon creator) ---
        # e.g. https://jp.mercari.com/item/m47344194219 — 田尻智 新ゲームデザイン 初版
        {
            'name': 'Tajiri Satoshi New Game Design (Mercari)',
            'platform': 'mercari',
            'keyword': '田尻智 新ゲームデザイン',
            'state_category': 'mercari_tajiri_new_game_design',
            'validators': [
                ['田尻智', '田尻 智', '田尻'],
                ['ゲームデザイン', 'game design'],
            ],
        },
        {
            'name': 'Tajiri Satoshi New Game Design (Yahoo)',
            'platform': 'yahoo',
            'keyword': '田尻智 新ゲームデザイン',
            'state_category': 'yahoo_tajiri_new_game_design',
            'validators': [
                ['田尻智', '田尻 智', '田尻'],
                ['ゲームデザイン', 'game design'],
            ],
        },
        {
            'name': 'Tajiri Satoshi New Game Design (eBay)',
            'platform': 'ebay',
            'keyword': '田尻智 新ゲームデザイン',
            'state_category': 'ebay_tajiri_new_game_design',
            'validators': [
                ['田尻智', '田尻', 'tajiri'],
                ['ゲームデザイン', 'game design'],
            ],
        },
        # --- Any Pokemon game, VGA-graded (any generation/platform) ---
        # e.g. https://jp.mercari.com/search?keyword=ポケットモンスター VGA
        {
            'name': 'Pokemon Game VGA-Graded (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター VGA',
            'state_category': 'mercari_pokemon_vga',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['vga'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Pokemon Game VGA-Graded (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ポケットモンスター VGA',
            'state_category': 'yahoo_pokemon_vga',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['vga'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Pokemon Game VGA-Graded (eBay)',
            'platform': 'ebay',
            'keyword': 'pocket monsters vga',
            'state_category': 'ebay_pokemon_vga',
            'validators': [
                ['pocket monster', 'pokemon', 'pokémon'],
                ['vga'],
            ],
            'exclude': ['plush', 'figure', 'card'],
        },
        # --- Any Pokemon game, CGC-graded (any generation/platform) ---
        {
            'name': 'Pokemon Game CGC-Graded (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター CGC',
            'state_category': 'mercari_pokemon_cgc',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['cgc'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Pokemon Game CGC-Graded (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ポケットモンスター CGC',
            'state_category': 'yahoo_pokemon_cgc',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                ['cgc'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Pokemon Game CGC-Graded (eBay)',
            'platform': 'ebay',
            'keyword': 'pocket monsters cgc',
            'state_category': 'ebay_pokemon_cgc',
            'validators': [
                ['pocket monster', 'pokemon', 'pokémon'],
                ['cgc'],
            ],
            'exclude': ['plush', 'figure', 'card'],
        },
        # --- Final Fantasy (Famicom), VGA-graded ---
        {
            'name': 'Final Fantasy Famicom VGA-Graded (Mercari)',
            'platform': 'mercari',
            'keyword': 'ファイナルファンタジー ファミコン VGA',
            'state_category': 'mercari_ff_famicom_vga',
            'validators': [
                ['ファイナルファンタジー', 'final fantasy'],
                ['vga'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Final Fantasy Famicom VGA-Graded (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ファイナルファンタジー ファミコン VGA',
            'state_category': 'yahoo_ff_famicom_vga',
            'validators': [
                ['ファイナルファンタジー', 'final fantasy'],
                ['vga'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Final Fantasy Famicom VGA-Graded (eBay)',
            'platform': 'ebay',
            'keyword': 'final fantasy famicom vga',
            'state_category': 'ebay_ff_famicom_vga',
            'validators': [
                ['final fantasy'],
                ['vga'],
            ],
            'exclude': ['plush', 'figure', 'card'],
        },
        # --- Final Fantasy (Famicom), CGC-graded ---
        {
            'name': 'Final Fantasy Famicom CGC-Graded (Mercari)',
            'platform': 'mercari',
            'keyword': 'ファイナルファンタジー ファミコン CGC',
            'state_category': 'mercari_ff_famicom_cgc',
            'validators': [
                ['ファイナルファンタジー', 'final fantasy'],
                ['cgc'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Final Fantasy Famicom CGC-Graded (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ファイナルファンタジー ファミコン CGC',
            'state_category': 'yahoo_ff_famicom_cgc',
            'validators': [
                ['ファイナルファンタジー', 'final fantasy'],
                ['cgc'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Final Fantasy Famicom CGC-Graded (eBay)',
            'platform': 'ebay',
            'keyword': 'final fantasy famicom cgc',
            'state_category': 'ebay_ff_famicom_cgc',
            'validators': [
                ['final fantasy'],
                ['cgc'],
            ],
            'exclude': ['plush', 'figure', 'card'],
        },
        # --- Dragon Quest (Famicom), VGA-graded ---
        {
            'name': 'Dragon Quest Famicom VGA-Graded (Mercari)',
            'platform': 'mercari',
            'keyword': 'ドラゴンクエスト ファミコン VGA',
            'state_category': 'mercari_dq_famicom_vga',
            'validators': [
                ['ドラゴンクエスト', 'ドラクエ', 'dragon quest'],
                ['vga'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Dragon Quest Famicom VGA-Graded (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ドラゴンクエスト ファミコン VGA',
            'state_category': 'yahoo_dq_famicom_vga',
            'validators': [
                ['ドラゴンクエスト', 'ドラクエ', 'dragon quest'],
                ['vga'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Dragon Quest Famicom VGA-Graded (eBay)',
            'platform': 'ebay',
            'keyword': 'dragon quest famicom vga',
            'state_category': 'ebay_dq_famicom_vga',
            'validators': [
                ['dragon quest', 'dragon warrior'],
                ['vga'],
            ],
            'exclude': ['plush', 'figure', 'card'],
        },
        # --- Dragon Quest (Famicom), CGC-graded ---
        {
            'name': 'Dragon Quest Famicom CGC-Graded (Mercari)',
            'platform': 'mercari',
            'keyword': 'ドラゴンクエスト ファミコン CGC',
            'state_category': 'mercari_dq_famicom_cgc',
            'validators': [
                ['ドラゴンクエスト', 'ドラクエ', 'dragon quest'],
                ['cgc'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Dragon Quest Famicom CGC-Graded (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ドラゴンクエスト ファミコン CGC',
            'state_category': 'yahoo_dq_famicom_cgc',
            'validators': [
                ['ドラゴンクエスト', 'ドラクエ', 'dragon quest'],
                ['cgc'],
            ],
            'exclude': ['カード', 'ぬいぐるみ', 'フィギュア'],
        },
        {
            'name': 'Dragon Quest Famicom CGC-Graded (eBay)',
            'platform': 'ebay',
            'keyword': 'dragon quest famicom cgc',
            'state_category': 'ebay_dq_famicom_cgc',
            'validators': [
                ['dragon quest', 'dragon warrior'],
                ['cgc'],
            ],
            'exclude': ['plush', 'figure', 'card'],
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

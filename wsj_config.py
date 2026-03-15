"""
Configuration for the Manga Scanner.
Monitors WSJ first appearance issues, Vol 1 first editions, and other collectible manga.
Uses separate Telegram bot/chat from the Pokemon (no-rarity) scanner.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class WSJConfig:
    """WSJ manga monitor configuration."""

    # Separate Telegram bot for manga alerts
    TELEGRAM_BOT_TOKEN: str = os.getenv('WSJ_TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('WSJ_TELEGRAM_CHAT_ID', '')

    # File paths
    BASE_DIR: Path = Path(__file__).parent
    DATA_DIR: Path = BASE_DIR / 'data'
    STATE_FILE: Path = DATA_DIR / 'wsj_seen_listings.json'
    LOG_FILE: Path = DATA_DIR / 'wsj_monitor.log'

    # Global exclude terms for simple searches
    GLOBAL_EXCLUDE: list[str] = [
        'reprint', 'reproduction',
        '再版', '重版', '復刻', '復刻版', '再刷', '複製',
    ]

    # -----------------------------------------------------------------------
    # WSJ SERIES — first appearance issues (use is_relevant_listing filtering)
    # -----------------------------------------------------------------------

    SERIES = {
        'naruto': {
            'name': 'NARUTO',
            'author': '岸本斉史',
            'author_en': 'Kishimoto Masashi',
            'wsj_issue': 'WSJ 1999 #43',
            'wsj_year': '1999',
            'wsj_number': '43',
            'wsj_desc': 'NARUTO Chapter 1 - 週刊少年ジャンプ 1999年43号',
            'ebay_queries': [
                'weekly shonen jump 1999 43 naruto',
                'shonen jump naruto first appearance 1999',
                '週刊少年ジャンプ 1999 43 NARUTO',
                'shonen jump 1999 #43 naruto',
            ],
            'mercari_queries': [
                '週刊少年ジャンプ 1999年43号',
                '少年ジャンプ 1999 43号 NARUTO',
                'NARUTO 新連載号 ジャンプ 1999',
                '週刊少年ジャンプ 1999 43号',
                'ジャンプ 1999 43号',
                'ナルト 新連載 ジャンプ',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1999年 43号',
                '少年ジャンプ 1999 43号 ナルト',
                'NARUTO 新連載 ジャンプ 1999',
                '週刊少年ジャンプ 1999 43',
            ],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'boruto', 'フィギュア', 'カードゲーム',
            ],
        },

        'bleach': {
            'name': 'BLEACH',
            'author': '久保帯人',
            'author_en': 'Kubo Tite',
            'wsj_issue': 'WSJ 2001 #36-37',
            'wsj_year': '2001',
            'wsj_number': '36',
            'wsj_desc': 'BLEACH Chapter 1 - 週刊少年ジャンプ 2001年36・37合併号',
            'ebay_queries': [
                'weekly shonen jump 2001 36 bleach',
                'shonen jump bleach first appearance 2001',
                '週刊少年ジャンプ 2001 36 BLEACH',
                'shonen jump 2001 #36 bleach',
            ],
            'mercari_queries': [
                '週刊少年ジャンプ 2001年36号',
                '少年ジャンプ 2001年36・37合併号',
                '少年ジャンプ 2001 36号 BLEACH',
                'BLEACH 新連載号 ジャンプ 2001',
                'ジャンプ 2001 36号',
                'BLEACH 新連載 ジャンプ',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 2001年 36号',
                '少年ジャンプ 2001 36・37 BLEACH',
                'BLEACH 新連載 ジャンプ 2001',
                '週刊少年ジャンプ 2001 36',
            ],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
                'cleaning', 'laundry', 'disinfect', '漂白',
            ],
        },

        'yugioh': {
            'name': '遊☆戯☆王 / Yu-Gi-Oh!',
            'author': '高橋和希',
            'author_en': 'Takahashi Kazuki',
            'wsj_issue': 'WSJ 1996 #42',
            'wsj_year': '1996',
            'wsj_number': '42',
            'wsj_desc': 'Yu-Gi-Oh! Chapter 1 - 週刊少年ジャンプ 1996年42号',
            'ebay_queries': [
                'weekly shonen jump 1996 42 yugioh',
                'weekly shonen jump 1996 42 yu-gi-oh',
                'shonen jump yu-gi-oh first appearance 1996',
                '週刊少年ジャンプ 1996 42 遊戯王',
            ],
            'mercari_queries': [
                '週刊少年ジャンプ 1996年42号',
                '少年ジャンプ 1996 42号 遊戯王',
                '遊戯王 新連載号 ジャンプ 1996',
                '遊☆戯☆王 新連載 ジャンプ 1996',
                'ジャンプ 1996 42号',
                '遊戯王 ジャンプ 掲載号',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1996年 42号',
                '少年ジャンプ 1996 42号 遊戯王',
                '遊戯王 新連載 ジャンプ 1996',
                '週刊少年ジャンプ 1996 42',
            ],
            'exclude_keywords': [
                'ocg', 'duel monsters card', 'trading card', 'tcg',
                'card game', 'figure', 'figurine', 'dvd', 'blu-ray',
                'フィギュア', 'カードゲーム', 'トレーディングカード',
            ],
            'mercari_urls': [
                'https://jp.mercari.com/search?keyword=%E9%81%8A%E6%88%AF%E7%8E%8B%201%E5%B7%BB%20%E5%88%9D%E7%89%88&sort=created_time&order=desc',
            ],
        },

        'dragonball': {
            'name': 'ドラゴンボール / Dragon Ball',
            'author': '鳥山明',
            'author_en': 'Toriyama Akira',
            'wsj_issue': 'WSJ 1984 #51',
            'wsj_year': '1984',
            'wsj_number': '51',
            'wsj_desc': 'Dragon Ball Chapter 1 - 週刊少年ジャンプ 1984年51号',
            'ebay_queries': [
                'weekly shonen jump 1984 51 dragon ball',
                'shonen jump dragon ball first appearance 1984',
                '週刊少年ジャンプ 1984 51 ドラゴンボール',
                'shonen jump 1984 51 toriyama',
            ],
            'mercari_queries': [
                '週刊少年ジャンプ 1984年51号',
                '少年ジャンプ 1984 51号 ドラゴンボール',
                'ドラゴンボール 新連載号 ジャンプ 1984',
                '鳥山明 ジャンプ 1984 51',
                'ジャンプ 1984 51号',
                'ドラゴンボール 新連載 ジャンプ',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1984年 51号',
                '少年ジャンプ 1984 51号 ドラゴンボール',
                'ドラゴンボール 新連載 ジャンプ 1984',
                '鳥山明 ジャンプ 1984 51',
            ],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'super', 'gt', 'フィギュア',
                'カードゲーム', 'トレーディングカード',
                'cushion', 'クッション', 'complete set', 'full color',
            ],
        },

        'hxh': {
            'name': 'HUNTER×HUNTER',
            'author': '冨樫義博',
            'author_en': 'Togashi Yoshihiro',
            'wsj_issue': 'WSJ 1998 #14',
            'wsj_year': '1998',
            'wsj_number': '14',
            'wsj_desc': 'Hunter×Hunter Chapter 1 - 週刊少年ジャンプ 1998年14号',
            'ebay_queries': [
                'weekly shonen jump 1998 14 hunter',
                'shonen jump hunter x hunter first appearance 1998',
                '週刊少年ジャンプ 1998 14 HUNTER',
                'shonen jump 1998 #14 hunter',
            ],
            'mercari_queries': [
                '週刊少年ジャンプ 1998年14号',
                '少年ジャンプ 1998 14号 HUNTER',
                'HUNTER×HUNTER 新連載号 ジャンプ 1998',
                'ハンターハンター 新連載 ジャンプ 1998',
                'ジャンプ 1998 14号',
                'ハンターハンター ジャンプ 掲載号',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1998年 14号',
                '少年ジャンプ 1998 14号 HUNTER',
                'HUNTER×HUNTER 新連載 ジャンプ 1998',
                '週刊少年ジャンプ 1998 14',
            ],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
            ],
        },

        'romance_dawn': {
            'name': 'ROMANCE DAWN (One Piece prototype)',
            'author': '尾田栄一郎',
            'author_en': 'Oda Eiichiro',
            'wsj_issue': 'WSJ 1996 #41',
            'wsj_year': '1996',
            'wsj_number': '41',
            'wsj_desc': 'Romance Dawn one-shot - 週刊少年ジャンプ 1996年41号 (Sexy Commando Gaiden cover)',
            'ebay_queries': [
                'weekly shonen jump 1996 41',
                'shonen jump 1996 #41 romance dawn',
                '週刊少年ジャンプ 1996 41',
                'shonen jump 1996 41 one piece romance dawn',
                'weekly shonen jump 1996 no 41',
            ],
            'mercari_queries': [
                '週刊少年ジャンプ 1996年41号',
                '少年ジャンプ 1996 41号',
                'ROMANCE DAWN ジャンプ 1996',
                'ロマンスドーン ジャンプ 1996',
                'ジャンプ 1996 41号',
                'ロマンスドーン 掲載号',
                'ロマンスドーン ジャンプ',
                '週刊少年ジャンプ 41号 ロマンスドーン',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1996年 41号',
                '少年ジャンプ 1996 41号',
                'ROMANCE DAWN ジャンプ 1996',
                '週刊少年ジャンプ 1996 41',
            ],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
            ],
        },

        'jojo': {
            'name': "JoJo's Bizarre Adventure",
            'author': '荒木飛呂彦',
            'author_en': 'Araki Hirohiko',
            'wsj_issue': 'WSJ 1987 #1-2',
            'wsj_year': '1987',
            'wsj_number': '1',
            'wsj_desc': "JoJo's Bizarre Adventure Chapter 1 - 週刊少年ジャンプ 1987年1・2合併号",
            'ebay_queries': [
                'weekly shonen jump 1987 jojo',
                'shonen jump 1987 1 jojo bizarre',
                '週刊少年ジャンプ 1987 ジョジョ',
            ],
            'mercari_queries': [
                '週刊少年ジャンプ 1987 1・2 ジョジョ',
                '少年ジャンプ 1987 ジョジョ 新連載',
                'ジョジョ 新連載号 ジャンプ 1987',
                'ジャンプ 1987 1号 ジョジョ',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1987 1・2 ジョジョ',
                '少年ジャンプ 1987 ジョジョ',
                'ジョジョ 新連載 ジャンプ 1987',
            ],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
                'jojolion', 'jojolands', 'stone ocean', 'steel ball',
            ],
        },

        'onepiece_ch1': {
            'name': 'ONE PIECE Ch.1 (WSJ 1997 #34)',
            'author': '尾田栄一郎',
            'author_en': 'Oda Eiichiro',
            'wsj_issue': 'WSJ 1997 #34',
            'wsj_year': '1997',
            'wsj_number': '34',
            'wsj_desc': 'One Piece Chapter 1 - 週刊少年ジャンプ 1997年34号',
            'ebay_queries': [
                'weekly shonen jump 1997 34',
                'weekly shonen jump 1997 vol 34',
                'shonen jump 1997 #34 one piece',
                '週刊少年ジャンプ 1997 34 ワンピース',
            ],
            'mercari_queries': [
                '週刊少年ジャンプ 1997年34号',
                '少年ジャンプ 1997 34号 ワンピース',
                'ONE PIECE 新連載号 ジャンプ 1997',
                'ジャンプ 1997 34号',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1997年 34号',
                '少年ジャンプ 1997 34号',
                'ONE PIECE 新連載 ジャンプ 1997',
                '週刊少年ジャンプ 1997 34',
            ],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
            ],
        },
    }

    # -----------------------------------------------------------------------
    # SIMPLE SEARCHES — Vol 1 first editions, CoroCoro, Comic News, etc.
    # These use basic AND/OR validator matching (not WSJ issue regex).
    # Searched via Mercari keyword, Yahoo Auctions keyword, or raw Mercari URL.
    # -----------------------------------------------------------------------

    SIMPLE_SEARCHES: list[dict] = [
        {
            'name': 'Naruto Vol 1 First Edition',
            'mercari_keyword': 'naruto 1巻 初版',
            'yahoo_keyword': 'naruto 1巻 初版',
            'state_category': 'simple_naruto_v1',
            'validators': [['ナルト', 'naruto'], ['1巻']],
        },
        {
            'name': 'CoroCoro Comic Nov 1996',
            'mercari_keyword': 'コロコロコミック 1996年 11月号',
            'yahoo_keyword': 'コロコロコミック 1996年 11月号',
            'state_category': 'simple_corocoro_nov96',
            'validators': [['コロコロ', 'corocoro'], ['1996'], ['11']],
        },
        {
            'name': 'Yu-Gi-Oh Vol 1 初版',
            'mercari_keyword': '遊戯王 1巻 初版',
            'yahoo_keyword': '遊戯王 1巻 初版',
            'state_category': 'simple_yugioh_v1',
            'validators': [
                ['遊戯王', 'yugioh', 'yu-gi-oh'],
                ['1巻'],
                ['初版', '第1刷', '第一刷'],
            ],
        },
        {
            'name': 'One Piece Vol 1 初版',
            'mercari_keyword': 'ワンピース 1巻 初版 第1刷',
            'yahoo_keyword': 'ワンピース 1巻 初版 第1刷',
            'state_category': 'simple_onepiece_v1',
            'validators': [
                ['ワンピース', 'onepiece', 'one piece'],
                ['1巻'],
                ['初版', '第1刷', '第一刷'],
            ],
        },
        {
            'name': 'BLEACH Vol 1 初版',
            'mercari_keyword': 'BLEACH 初版1巻',
            'yahoo_keyword': 'BLEACH 初版1巻',
            'state_category': 'simple_bleach_v1',
            'validators': [
                ['bleach', 'ブリーチ'],
                ['1巻'],
                ['初版', '第1刷', '第一刷'],
            ],
        },
        {
            'name': 'Comic News 195',
            'mercari_keyword': 'コミックニュース195',
            'yahoo_keyword': 'コミックニュース195',
            'state_category': 'simple_comic_news_195',
            'validators': [['コミックニュース', 'comic news'], ['195']],
        },
    ]

    @classmethod
    def validate(cls) -> list[str]:
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append('WSJ_TELEGRAM_BOT_TOKEN')
        if not cls.TELEGRAM_CHAT_ID:
            missing.append('WSJ_TELEGRAM_CHAT_ID')
        return missing

    @classmethod
    def is_telegram_configured(cls) -> bool:
        return bool(cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID)


# Ensure data directory exists
WSJConfig.DATA_DIR.mkdir(parents=True, exist_ok=True)

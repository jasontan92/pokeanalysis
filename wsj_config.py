"""
Configuration for the Manga Scanner.
Monitors WSJ first appearance issues, Vol 1 first editions, and other collectible manga on Japanese sites.
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
            'mercari_queries': [
                '週刊少年ジャンプ 1999年43号',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1999年 43号',
                'NARUTO 新連載 ジャンプ 43号',
            ],
            'title_identifiers': ['NARUTO', 'ナルト', '岸本斉史'],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'boruto', 'フィギュア', 'カードゲーム',
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
            'mercari_queries': [
                '週刊少年ジャンプ 1996年42号',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1996年 42号',
                '遊戯王 新連載 ジャンプ 42号',
            ],
            'title_identifiers': ['遊戯王', 'Yu-Gi-Oh', '高橋和希'],
            'exclude_keywords': [
                'ocg', 'duel monsters card', 'trading card', 'tcg',
                'card game', 'figure', 'figurine', 'dvd', 'blu-ray',
                'フィギュア', 'カードゲーム', 'トレーディングカード',
            ],
            # Yu-Gi-Oh Vol 1 初版 is handled by SIMPLE_SEARCHES below
        },

        'romance_dawn': {
            'name': 'ROMANCE DAWN (One Piece prototype)',
            'author': '尾田栄一郎',
            'author_en': 'Oda Eiichiro',
            'wsj_issue': 'WSJ 1996 #41',
            'wsj_year': '1996',
            'wsj_number': '41',
            'wsj_desc': 'Romance Dawn one-shot - 週刊少年ジャンプ 1996年41号 (Sexy Commando Gaiden cover)',
            'mercari_queries': [
                '週刊少年ジャンプ 1996年41号',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1996年 41号',
                'ロマンスドーン ジャンプ 41号',
            ],
            'title_identifiers': ['ロマンスドーン', 'ROMANCE DAWN', '尾田栄一郎'],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
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
            'mercari_queries': [
                '週刊少年ジャンプ 1997年34号',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1997年 34号',
                'ワンピース 新連載 ジャンプ 34号',
            ],
            'title_identifiers': ['ワンピース', 'ONE PIECE', '尾田栄一郎'],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
            ],
        },

        'bleach': {
            'name': 'BLEACH',
            'author': '久保帯人',
            'author_en': 'Kubo Tite',
            'wsj_issue': 'WSJ 2001 #36-37',
            'wsj_year': '2001',
            'wsj_number': '36・37',
            'wsj_desc': 'BLEACH Chapter 1 - 週刊少年ジャンプ 2001年36・37合併号',
            'mercari_queries': [
                '週刊少年ジャンプ 2001年36',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 2001年 36',
                'BLEACH 新連載 ジャンプ 36号',
            ],
            'title_identifiers': ['BLEACH', 'ブリーチ', '久保帯人'],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
                'thousand year', '千年血戦',
            ],
        },

        'jojo': {
            'name': 'ジョジョの奇妙な冒険 / JoJo\'s Bizarre Adventure',
            'author': '荒木飛呂彦',
            'author_en': 'Araki Hirohiko',
            'wsj_issue': 'WSJ 1987 #1-2',
            'wsj_year': '1987',
            'wsj_number': '1・2',
            'wsj_desc': 'JoJo Chapter 1 - 週刊少年ジャンプ 1987年1・2合併号',
            'mercari_queries': [
                '週刊少年ジャンプ 1987 1-2',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1987 1-2',
                'ジョジョ 新連載 ジャンプ 1-2',
            ],
            'title_identifiers': ['ジョジョ', 'JOJO', '荒木飛呂彦'],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
                'reprint', 'reproduction', '復刻', '復刻版', 'リプリント',
                '再版', '再録', '愛蔵版', '完全版', '文庫版', '新装版',
            ],
        },

        'dragonball': {
            'name': 'DRAGON BALL',
            'author': '鳥山明',
            'author_en': 'Toriyama Akira',
            'wsj_issue': 'WSJ 1984 #51',
            'wsj_year': '1984',
            'wsj_number': '51',
            'wsj_desc': 'Dragon Ball Chapter 1 - 週刊少年ジャンプ 1984年51号',
            'mercari_queries': [
                '週刊少年ジャンプ 1984年51号',
                'ドラゴンボール 新連載号 ジャンプ 1984',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1984年 51号',
                'ドラゴンボール 新連載 ジャンプ 1984',
                'ドラゴンボール 新連載 ジャンプ 51号',
            ],
            'title_identifiers': ['ドラゴンボール', 'DRAGON BALL', '鳥山明'],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
                'super', 'スーパー', 'daima',
            ],
        },

        'hxh': {
            'name': 'HUNTER×HUNTER',
            'author': '冨樫義博',
            'author_en': 'Togashi Yoshihiro',
            'wsj_issue': 'WSJ 1998 #14',
            'wsj_year': '1998',
            'wsj_number': '14',
            'wsj_desc': 'HUNTER×HUNTER Chapter 1 - 週刊少年ジャンプ 1998年14号',
            'mercari_queries': [
                '週刊少年ジャンプ 1998年14号',
            ],
            'yahoo_queries': [
                '週刊少年ジャンプ 1998年 14号',
                'HUNTER×HUNTER 新連載 ジャンプ 14号',
            ],
            'title_identifiers': ['HUNTER', 'ハンター', '冨樫義博'],
            'exclude_keywords': [
                'trading card', 'tcg', 'card game', 'figure', 'figurine',
                'dvd', 'blu-ray', 'フィギュア', 'カードゲーム',
            ],
        },
    }

    # -----------------------------------------------------------------------
    # SIMPLE SEARCHES — Vol 1 first editions, CoroCoro, Comic News, etc.
    # These use basic AND/OR validator matching (not WSJ issue regex).
    # -----------------------------------------------------------------------

    SIMPLE_SEARCHES: list[dict] = [
        {
            'name': '犬夜叉 週刊少年サンデー 1996年50号',
            'mercari_keyword': '週刊少年サンデー 犬夜叉 1996年 50号',
            'mercari_url': 'https://jp.mercari.com/search?keyword=%E9%80%B1%E5%88%8A%E5%B0%91%E5%B9%B4%E3%82%B5%E3%83%B3%E3%83%87%E3%83%BC%20%E7%8A%AC%E5%A4%9C%E5%8F%89%201996%E5%B9%B4%2050%E5%8F%B7&sort=created_time&order=desc',
            'yahoo_keyword': '週刊少年サンデー 犬夜叉 1996年 50号',
            'state_category': 'simple_inuyasha_sunday_1996_50',
            'validators': [
                ['サンデー', 'sunday'],
                ['1996'],
                ['50'],
            ],
        },
        {
            'name': 'アニメージュ 1982年2月号',
            'mercari_keyword': 'アニメージュ 1982年2月号',
            'mercari_url': 'https://jp.mercari.com/search?keyword=%E3%82%A2%E3%83%8B%E3%83%A1%E3%83%BC%E3%82%B8%E3%83%A5%201982%E5%B9%B42%E6%9C%88%E5%8F%B7&sort=created_time&order=desc',
            'yahoo_keyword': 'アニメージュ 1982年 2月号',
            'state_category': 'simple_animage_1982_02',
            'validators': [
                ['アニメージュ', 'animage'],
                ['1982'],
                ['2'],
            ],
        },
        {
            'name': 'CoroCoro Comic 1996年11月号',
            'mercari_keyword': 'コロコロコミック 1996年 11月号',
            'mercari_url': 'https://jp.mercari.com/search?keyword=%E3%82%B3%E3%83%AD%E3%82%B3%E3%83%AD%E3%82%B3%E3%83%9F%E3%83%83%E3%82%AF%201996%E5%B9%B4%2011%E6%9C%88%E5%8F%B7&sort=created_time&order=desc',
            'yahoo_keyword': 'コロコロコミック 1996年 11月号',
            'state_category': 'simple_corocoro_1996',
            'validators': [
                ['コロコロ', 'corocoro'],
                ['1996'],
                ['11月', '十一月'],
            ],
        },
        {
            'name': 'Bessatsu CoroCoro Comic 1996',
            'mercari_keyword': '別冊コロコロコロ 1996',
            'mercari_url': 'https://jp.mercari.com/search?keyword=%E5%88%A5%E5%86%8A%E3%82%B3%E3%83%AD%E3%82%B3%E3%83%AD%E3%82%B3%201996&sort=created_time&order=desc',
            'yahoo_keyword': '別冊コロコロコミック 1996年',
            'state_category': 'simple_bessatsu_corocoro_1996',
            'validators': [['別冊'], ['コロコロ'], ['1996'], ['月刊', '特刊', '増刊', '号', '月号', 'comic', 'コミック']],
        },
        {
            'name': 'Digimon Vジャンプ 1999年1月号',
            'mercari_keyword': 'Vジャンプ 1999年1月号',
            'yahoo_keyword': 'Vジャンプ 1999年 1月号',
            'state_category': 'simple_digimon_vjump_1999_01',
            'validators': [
                ['Vジャンプ', 'V JUMP', 'ブイジャンプ', 'Ｖジャンプ', 'vジャンプ'],
                ['1999年1月'],
            ],
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
            'name': 'Dragon Ball Vol 1 初版',
            'mercari_keyword': 'ドラゴンボール 1巻 初版',
            'yahoo_keyword': 'ドラゴンボール 1巻 初版',
            'state_category': 'simple_dragonball_v1',
            'validators': [
                ['ドラゴンボール', 'dragon ball', 'dragonball', 'DRAGON BALL'],
                ['1巻'],
                ['初版', '第1刷', '第一刷'],
            ],
        },
        {
            'name': '電撃 RPG\'96',
            'mercari_url': 'https://jp.mercari.com/search?keyword=%E9%9B%BB%E6%92%83%20RPG%E2%80%9996&srsltid=AfmBOooDJCEu2u_xL7jc9cCXVCmu9RaoPcWQ4tUagAxb_De80gdOw84U&sort=created_time&order=desc',
            'yahoo_keyword': '電撃 RPG\'96',
            'state_category': 'simple_dengeki_rpg_96',
            'validators': [['電撃'], ['rpg', 'RPG'], ['96']],
        },
        {
            'name': '週刊少年ジャンプ 1989年 47号',
            'mercari_keyword': '週刊少年ジャンプ 1989年 47号',
            'yahoo_keyword': '週刊少年ジャンプ 1989年 47号',
            'state_category': 'simple_wsj_1989_47',
            'validators': [
                ['1989'],
                ['47'],
            ],
            'exclude': ['梱包'],
        },
        {
            'name': '週刊少年ジャンプ 1989年 2-3号',
            'mercari_keyword': '週刊少年ジャンプ 1989年 2-3号',
            'yahoo_keyword': '週刊少年ジャンプ 1989年 2-3号',
            'state_category': 'simple_wsj_1989_2_3',
            'validators': [
                ['1989'],
                ['2-3', '2・3', '2,3'],
            ],
            'exclude': ['梱包'],
        },
        {
            'name': '週刊少年ジャンプ 1990年 42号',
            'mercari_keyword': '週刊少年 1990年 42号',
            'yahoo_keyword': '週刊少年ジャンプ 1990年 42号',
            'state_category': 'simple_wsj_1990_42',
            'validators': [
                ['1990'],
                ['42'],
            ],
            'exclude': ['梱包'],
        },
        {
            'name': 'Pocket Monsters (Anakubo) (ポケットモンスター 巻)',
            'mercari_keyword': 'ポケットモンスター 巻',
            'mercari_url': 'https://jp.mercari.com/search?keyword=%E3%83%9D%E3%82%B1%E3%83%83%E3%83%88%E3%83%A2%E3%83%B3%E3%82%B9%E3%82%BF%E3%83%BC%20%E5%B7%BB&sort=created_time&order=desc',
            'yahoo_keyword': 'ポケットモンスター 巻',
            'state_category': 'simple_anakubo_pokemon_v1',
            'validators': [
                ['ポケットモンスター'],
                ['1', '一', '全'],
            ],
        },
        {
            'name': '穴久保 初版 (Anakubo first edition)',
            'mercari_keyword': '穴久保 初版',
            'yahoo_keyword': '穴久保 初版',
            'state_category': 'simple_anakubo_first_edition',
            'validators': [
                ['穴久保'],
                ['初版', '第1刷', '第一刷'],
            ],
        },
        {
            'name': '少年ジャンプ 1989年 1-2号',
            'mercari_keyword': '少年ジャンプ 1989年 1-2号',
            'mercari_url': 'https://jp.mercari.com/search?keyword=%E5%B0%91%E5%B9%B4%E3%82%B8%E3%83%A3%E3%83%B3%E3%83%97%201989%E5%B9%B4%201-2%E5%8F%B7&sort=created_time&order=desc',
            'yahoo_keyword': '少年ジャンプ 1989年 1-2号',
            'state_category': 'simple_wsj_1989_1_2',
            'validators': [
                ['1989'],
                ['1-2', '1・2', '1/2', 'No.1-2', '合併号', '1,2'],
            ],
        },
        {
            'name': 'Pokemon Red/Green Flyer (チラシ)',
            'mercari_keyword': 'ポケットモンスター 赤 緑 チラシ',
            'mercari_url': 'https://jp.mercari.com/search?keyword=%E3%83%9D%E3%82%B1%E3%83%83%E3%83%88%E3%83%A2%E3%83%B3%E3%82%B9%E3%82%BF%E3%83%BC%E3%80%80%E8%B5%A4%E3%80%80%E7%B7%91%E3%80%80%E3%83%81%E3%83%A9%E3%82%B7%E3%80%80&sort=created_time&order=desc',
            'yahoo_keyword': 'ポケットモンスター 赤 緑 チラシ',
            'state_category': 'simple_pokemon_rg_flyer',
            'validators': [
                ['チラシ'],
            ],
        },
        {
            'name': '週刊少年サンデー 2020年22・23号',
            'mercari_keyword': '週刊少年サンデー 2020年 22 23',
            'yahoo_keyword': '週刊少年サンデー 2020年 22 23',
            'state_category': 'simple_sunday_2020_22_23',
            'validators': [
                ['サンデー', 'sunday'],
                ['2020'],
                ['22', '23'],
            ],
        },
        {
            'name': '週刊少年マガジン 2005年17号',
            'mercari_keyword': '週刊少年マガジン 2005年 17号',
            'yahoo_keyword': '週刊少年マガジン 2005年 17号',
            'state_category': 'simple_magazine_2005_17',
            'validators': [
                ['週刊少年マガジン'],
                ['2005'],
                ['17'],
            ],
        },
        {
            'name': 'ヤングマガジン 1982年24号',
            'mercari_keyword': 'ヤングマガジン 1982年 24',
            'yahoo_keyword': 'ヤングマガジン 1982年 24',
            'state_category': 'simple_young_magazine_1982_24',
            'validators': [
                ['ヤングマガジン'],
                ['1982'],
                ['24'],
            ],
        },
        {
            'name': '週刊少年ジャンプ 2016年11号',
            'mercari_keyword': '週刊少年ジャンプ 2016年11号',
            'yahoo_keyword': '週刊少年ジャンプ 2016年 11号',
            'state_category': 'simple_wsj_2016_11',
            'validators': [
                ['ジャンプ'],
                ['2016'],
                ['11'],
            ],
        },
    ]

    # -----------------------------------------------------------------------
    # UNFILTERED MERCARI URLS — ping on ANY new result, no filtering at all
    # -----------------------------------------------------------------------

    UNFILTERED_MERCARI_URLS: list[dict] = [
        {
            'name': 'Romance Dawn WSJ 1996 (unfiltered)',
            'url': 'https://jp.mercari.com/search?keyword=%E9%80%B1%E5%88%8A%E5%B0%91%E5%B9%B4%E3%82%B8%E3%83%A3%E3%83%B3%E3%83%97%201996%20%20%E3%83%AD%E3%83%9E%E3%83%B3%E3%82%B9%E3%83%89%E3%83%BC%E3%83%B3&sort=created_time&order=desc',
            'state_category': 'unfiltered_romancedawn_1996',
        },
        {
            'name': 'Fresh Jump 1983年8月号',
            'url': 'https://jp.mercari.com/search?keyword=%E3%83%95%E3%83%AC%E3%83%83%E3%82%B7%E3%83%A5%E3%82%B8%E3%83%A3%E3%83%B3%E3%83%97%201983%E5%B9%B48%E6%9C%88%E5%8F%B7&sort=created_time&order=desc',
            'state_category': 'unfiltered_fresh_jump_1983_08',
        },
        {
            'name': '別冊少年マガジン 2009年10月号',
            'url': 'https://jp.mercari.com/search?keyword=%E5%88%A5%E5%86%8A%E5%B0%91%E5%B9%B4%E3%83%9E%E3%82%AC%E3%82%B8%E3%83%B3%202009%E5%B9%B410%E6%9C%88%E5%8F%B7&sort=created_time&order=desc',
            'state_category': 'unfiltered_bessatsu_2009_10',
            'validators': [
                ['別冊'],
                ['2009'],
                ['10'],
            ],
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

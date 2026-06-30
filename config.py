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

    # --- Famicom game search building blocks (Zelda / Mario / DQ / FF) ---
    # Condition: VGA OR CGC OR unopened. Keyword forces 未開封 on JP sites
    # (also narrows Yahoo so the franchise term doesn't flood the results).
    _FC_COND: list[str] = ['vga', 'cgc', 'wata', 'graded', '鑑定', '未開封', '未使用', 'sealed', 'unopened']
    # Positive gate: the title must prove it's an actual Famicom cartridge/disk,
    # not a Switch/SFC re-release or merch that merely names the franchise.
    _FC_MEDIUM: list[str] = [
        'ファミコン', 'ファミリーコンピュータ', 'ファミリーコンピューター',
        'ディスクシステム', 'hvc', 'fc', 'famicom', 'family computer',
    ]
    # Aggressive reject list: other consoles, merch, apparel, books, peripherals.
    _FC_EXCLUDE_JP: list[str] = [
        # other consoles / not the original cartridge
        'スーパーファミコン', 'スーファミ', 'sfc', 'super famicom', 'snes',
        'ニンテンドースイッチ', 'switch', 'ゲームボーイアドバンス', 'gba',
        'ニンテンドーds', '3ds', 'ツクダ', 'ゆ太郎', 'プレイステーション', 'ps1', 'ps2',
        # books / magazines / paper goods
        '攻略本', 'ガイドブック', '奥義大全書', 'ファンブック', '設定資料', '資料集',
        '記念book', '記念ブック', 'てれびくん', '雑誌', '増刊', 'コミック', '漫画',
        'カタログ', 'チラシ', 'カレンダー', '冊子',
        # apparel / cloth / textile
        '手ぬぐい', 'タオル', 'セーター', 'tシャツ', '靴下', 'パーカー', '帽子', 'キャップ',
        'マスク', 'ストッカー', 'タペストリー', 'のれん', 'クッション', 'ブランケット',
        # toys / figures / merch
        'フィギュア', 'ブリングアーツ', 'ぬいぐるみ', '人形', 'プライズ', 'ガチャ',
        '一番くじ', 'くじ', '缶バッジ', 'バッジ', 'ピンズ', 'メダル', '時計', '置物',
        'マグカップ', '食器', '弁当', 'ストラップ', 'キーホルダー', 'アクリル', 'マグネット',
        'プラモ', '模型', 'amiibo', 'アミーボ', 'ねんどろ',
        # accessories / peripherals
        'コントローラ', 'ケーブル', 'アダプタ', '周辺機器', '変換',
        # cards / stickers / stationery
        'カード', 'トレカ', 'シール', 'ステッカー', 'ブロマイド', '下敷き', 'トランプ',
        'ジグソー', 'パズル', 'クリアファイル', 'ノート', '鉛筆', '消しゴム',
        # music
        'サントラ', 'サウンドトラック', 'レコード',
        # generic merch grouping
        'グッズ', 'ポスター', 'ビーチボール', 'リュック', 'リュッサック', 'バッグ',
        'スマホ', 'iphone', 'ダイカット', 'go plus', 'poco', 'ぽこ', 'レゴ', 'lego',
    ]
    _FC_EXCLUDE_EN: list[str] = [
        'plush', 'figure', 'poster', 'keychain', 'keyring', 'sticker', 'decal',
        'card', 'trading card', 'strategy guide', 'guide book', 'guidebook',
        'magazine', 'comic', 'soundtrack', 'vinyl', 't-shirt', 'towel', 'mug', 'badge',
        'amiibo', 'super famicom', 'snes', 'sfc', 'super nintendo', 'switch',
        'game boy advance', 'gba', 'nintendo ds', '3ds', 'reproduction', 'repro', 'lego',
    ]
    # Pokemon unopened is scoped to Game Boy / Game Boy Color ONLY (the
    # collectible red/green/blue/yellow + gold/silver/crystal era). The gate
    # requires a Game Boy term; "ゲームボーイ" also matches "ゲームボーイアドバンス",
    # so GBA is rejected explicitly below. DS/3DS/Switch lack a GB term and
    # so fail the gate automatically.
    _PKMN_MEDIUM: list[str] = [
        'ゲームボーイ', 'game boy', 'gameboy', 'gb', 'gbc',
        'ゲームボーイカラー', 'game boy color',
    ]
    _PKMN_EXCLUDE: list[str] = [
        # later consoles (out of GB/GBC scope)
        'ゲームボーイアドバンス', 'アドバンス', 'advance', 'gba',
        'ニンテンドーds', 'nintendo ds', '3ds', 'switch', 'スイッチ',
        'ゲームキューブ', 'gamecube', 'wii',
        # cards / paper
        'カード', 'ポケカ', 'トレカ', 'プロモ', 'trading card', 'シール', 'ステッカー',
        'sticker', 'ブロマイド', 'クリアファイル', 'カレンダー', '下敷き', 'トランプ',
        'カードダス', 'シールダス', 'carddass', 'sealdass', 'sealldass', 'amada', 'アマダ',
        # figures / plush / toys
        'ぬいぐるみ', 'plush', 'フィギュア', 'figure', '人形', 'プライズ', 'ガチャ',
        '一番くじ', 'くじ', 'ナノブロック', 'プラモ', '模型', 'ジグソー', 'パズル',
        # apparel / accessories / merch
        'タオル', 'towel', 'tシャツ', 't-shirt', '靴下', '帽子', 'マスク', 'ポーチ',
        'バッグ', 'リュック', 'キーホルダー', 'keychain', 'アクリル', 'ストラップ',
        '缶バッジ', 'バッジ', 'badge', 'ピンズ', 'メダル', 'マグカップ', 'mug', '食器',
        '弁当', '時計', '置物', 'スマホ', 'iphone', '切り絵', 'マグネット',
        # music boxes / soundtracks / non-game GB-shaped novelties
        'サントラ', 'サウンドトラック', 'soundtrack', 'music', 'ミュージック',
        'さいせいマシン', 'レコード', 'vinyl', 'オルゴール',
        # accessories that pass the GB gate but aren't games
        'ケーブル', 'cable', '通信', '消しゴム', 'ケシゴム', 'プロテクター',
        'protector', 'スタンド', '収納', 'カバー', '電池', 'アダプタ',
        # substring traps
        'ソフトバンク', 'グッズ', 'ポスター', 'poster',
        # English merch / cards / fast-food toys (mostly eBay)
        'promo', 'holo', 'card', 'toy', 'meal', 'burger king', 'mcdonald',
        'coin', 'medal', 'magnet', 'box art',
    ]

    # Monitored searches — Pokemon game cartridges only
    # validators: list of lists — each inner list = alternatives (OR), all outer lists must pass (AND)
    # optional 'exclude': per-search extra exclude terms (on top of GLOBAL_EXCLUDE)
    MONITORED_SEARCHES: list[dict] = [
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
        # --- Pokemon GAMES (Game Boy / GBC only), VGA-graded ---
        # Game-medium gate (_PKMN_MEDIUM) requires a Game Boy term in the
        # title, so graded CARDS (Carddass/Sealdass) are rejected.
        {
            'name': 'Pokemon Game VGA-Graded (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター ゲームボーイ VGA',
            'state_category': 'mercari_pokemon_vga',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                _PKMN_MEDIUM,
                ['vga'],
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        {
            'name': 'Pokemon Game VGA-Graded (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ポケットモンスター ゲームボーイ VGA',
            'state_category': 'yahoo_pokemon_vga',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                _PKMN_MEDIUM,
                ['vga'],
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        {
            'name': 'Pokemon Game VGA-Graded (eBay)',
            'platform': 'ebay',
            'keyword': 'pokemon game boy vga',
            'state_category': 'ebay_pokemon_vga',
            'validators': [
                ['pocket monster', 'pokemon', 'pokémon'],
                _PKMN_MEDIUM,
                ['vga'],
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        # --- Pokemon GAMES (Game Boy / GBC only), CGC-graded ---
        {
            'name': 'Pokemon Game CGC-Graded (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター ゲームボーイ CGC',
            'state_category': 'mercari_pokemon_cgc',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                _PKMN_MEDIUM,
                ['cgc'],
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        {
            'name': 'Pokemon Game CGC-Graded (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ポケットモンスター ゲームボーイ CGC',
            'state_category': 'yahoo_pokemon_cgc',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                _PKMN_MEDIUM,
                ['cgc'],
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        {
            'name': 'Pokemon Game CGC-Graded (eBay)',
            'platform': 'ebay',
            'keyword': 'pokemon game boy cgc',
            'state_category': 'ebay_pokemon_cgc',
            'validators': [
                ['pocket monster', 'pokemon', 'pokémon'],
                _PKMN_MEDIUM,
                ['cgc'],
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        # --- Famicom games (Zelda / Mario / DQ / FF): VGA OR CGC OR unopened ---
        # Zelda
        {
            'name': 'Zelda Famicom VGA/CGC/Sealed (Mercari)',
            'platform': 'mercari',
            'keyword': 'ゼルダの伝説 ファミコン 未開封',
            'state_category': 'mercari_zelda_famicom',
            'validators': [['ゼルダの伝説', 'ゼルダ', 'zelda'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Zelda Famicom VGA/CGC/Sealed (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ゼルダの伝説 ファミコン 未開封',
            'state_category': 'yahoo_zelda_famicom',
            'validators': [['ゼルダの伝説', 'ゼルダ', 'zelda'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Zelda Famicom VGA/CGC/Sealed (eBay)',
            'platform': 'ebay',
            'keyword': 'zelda famicom',
            'state_category': 'ebay_zelda_famicom',
            'validators': [['zelda'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_EN,
        },
        # Mario
        {
            'name': 'Mario Famicom VGA/CGC/Sealed (Mercari)',
            'platform': 'mercari',
            'keyword': 'スーパーマリオ ファミコン 未開封',
            'state_category': 'mercari_mario_famicom',
            'validators': [['スーパーマリオ', 'マリオ', 'mario'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Mario Famicom VGA/CGC/Sealed (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'スーパーマリオ ファミコン 未開封',
            'state_category': 'yahoo_mario_famicom',
            'validators': [['スーパーマリオ', 'マリオ', 'mario'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Mario Famicom VGA/CGC/Sealed (eBay)',
            'platform': 'ebay',
            'keyword': 'super mario famicom',
            'state_category': 'ebay_mario_famicom',
            'validators': [['mario'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_EN,
        },
        # Dragon Quest
        {
            'name': 'Dragon Quest Famicom VGA/CGC/Sealed (Mercari)',
            'platform': 'mercari',
            'keyword': 'ドラゴンクエスト ファミコン 未開封',
            'state_category': 'mercari_dq_famicom',
            'validators': [['ドラゴンクエスト', 'ドラクエ', 'dragon quest'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Dragon Quest Famicom VGA/CGC/Sealed (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ドラゴンクエスト ファミコン 未開封',
            'state_category': 'yahoo_dq_famicom',
            'validators': [['ドラゴンクエスト', 'ドラクエ', 'dragon quest'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Dragon Quest Famicom VGA/CGC/Sealed (eBay)',
            'platform': 'ebay',
            'keyword': 'dragon quest famicom',
            'state_category': 'ebay_dq_famicom',
            'validators': [['dragon quest', 'dragon warrior'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_EN,
        },
        # Final Fantasy
        {
            'name': 'Final Fantasy Famicom VGA/CGC/Sealed (Mercari)',
            'platform': 'mercari',
            'keyword': 'ファイナルファンタジー ファミコン 未開封',
            'state_category': 'mercari_ff_famicom',
            'validators': [['ファイナルファンタジー', 'final fantasy'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Final Fantasy Famicom VGA/CGC/Sealed (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ファイナルファンタジー ファミコン 未開封',
            'state_category': 'yahoo_ff_famicom',
            'validators': [['ファイナルファンタジー', 'final fantasy'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Final Fantasy Famicom VGA/CGC/Sealed (eBay)',
            'platform': 'ebay',
            'keyword': 'final fantasy famicom',
            'state_category': 'ebay_ff_famicom',
            'validators': [['final fantasy'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_EN,
        },
        # --- Pokemon games, unopened (未開封) — game-medium gated ---
        {
            'name': 'Pokemon Game Unopened (Mercari)',
            'platform': 'mercari',
            'keyword': 'ポケットモンスター ゲームボーイ 未開封',
            'state_category': 'mercari_pokemon_unopened',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                _PKMN_MEDIUM,
                ['未開封', '未使用', 'sealed', 'unopened'],
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        {
            'name': 'Pokemon Game Unopened (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ポケットモンスター ゲームボーイ 未開封',
            'state_category': 'yahoo_pokemon_unopened',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                _PKMN_MEDIUM,
                ['未開封', '未使用', 'sealed', 'unopened'],
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        {
            'name': 'Pokemon Game Unopened (eBay)',
            'platform': 'ebay',
            'keyword': 'pokemon game boy sealed',
            'state_category': 'ebay_pokemon_unopened',
            'validators': [
                ['pocket monster', 'pokemon', 'pokémon'],
                _PKMN_MEDIUM,
                ['sealed', 'unopened', '未開封'],
            ],
            'exclude': _PKMN_EXCLUDE,
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

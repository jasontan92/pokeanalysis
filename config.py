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

    # eBay-only: keep JAPANESE-version listings. Mercari/Yahoo are inherently
    # Japanese so this is applied only to eBay results (see monitor.py).
    EBAY_JP_MARKERS: list[str] = [
        'japanese', 'japan', 'jpn', 'ntsc-j', 'ntscj', 'ntsc j',
        'famicom', 'スーパーファミコン', 'ファミコン', 'ディスクシステム',
        'pocket monsters', 'ポケットモンスター',
        'ファイナルファンタジー', 'ドラゴンクエスト', 'ゼルダ', 'マリオ',
    ]
    EBAY_REGION_EXCLUDE: list[str] = [
        'pal', 'spanish', 'edición', 'edicion', 'español', 'europe', 'european',
        'deutsch', 'german', 'français', 'french', 'italiano', 'italian',
        'australia', 'korea', 'korean', 'us version', 'usa version',
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
        # Super Famicom now allowed (Zelda/Mario/DQ/FF SFC titles)
        'スーパーファミコン', 'スーファミ', 'super famicom', 'sfc', 'snes', 'super nintendo',
        # Nintendo 64 now allowed (Zelda Ocarina/Majora, Super Mario 64, etc.)
        # Specific console terms only ('64' alone matches product codes).
        'ニンテンドー64', 'ニンテンドウ64', 'nintendo64', 'nintendo 64', 'n64', 'ロクヨン',
        # Original Game Boy allowed (Link's Awakening, Super Mario Land, etc).
        # NOTE: "ゲームボーイカラー"/"ゲームボーイアドバンス" contain "ゲームボーイ",
        # so GBC and GBA/SP are rejected explicitly in _FC_EXCLUDE_JP/EN.
        'ゲームボーイ', 'game boy', 'gameboy', 'gb',
    ]
    # Aggressive reject list: other consoles, merch, apparel, books, peripherals.
    _FC_EXCLUDE_JP: list[str] = [
        # other consoles / not the original cartridge (Famicom/SFC/N64/GB allowed)
        'ニンテンドースイッチ', 'switch',
        # GBC and GBA/SP rejected (they'd otherwise match the "ゲームボーイ" gate)
        'ゲームボーイカラー', 'game boy color', 'gameboy color', 'gbc',
        'ゲームボーイアドバンス', 'game boy advance', 'gameboy advance', 'gba', 'アドバンス',
        'ゲームボーイミクロ', 'ニンテンドーds', '3ds', 'ツクダ', 'ゆ太郎',
        'プレイステーション', 'ps1', 'ps2',
        'wii', 'ゲームキューブ', 'gamecube',
        'バーチャルコンソール', 'virtual console', 'ミニ', 'クラシックミニ',
        # cartridge/carry cases & other non-game accessories
        '収納', 'キャリーケース', 'キャリング', '空ケース', 'ケースのみ',
        'プラスティック', 'プラスチック', 'カセットケース',
        # toys / media that collide with the "64" keyword
        'ホットウィール', 'hot wheels', 'マテル', 'mattel', 'cd', 'dvd', 'ホットウィールズ',
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
        'amiibo', 'switch',
        'game boy color', 'gameboy color', 'gbc',
        'game boy advance', 'gameboy advance', 'gba', 'advance sp',
        'nintendo ds', '3ds', 'reproduction', 'repro', 'lego',
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
    # Relaxed game-indicator gate for UNOPENED (per-color) searches: a real
    # sealed game usually says one of these even without naming the console,
    # so console-less listings (e.g. "ポケットモンスター 青 バーコード有り") pass
    # while merch/cards (which lack these) are dropped.
    _PKMN_GAME: list[str] = [
        'ゲームボーイ', 'game boy', 'gameboy', 'gb', 'gbc', 'ゲームボーイカラー',
        'ソフト', 'software', 'カセット', 'cartridge',
        'バージョン', 'version', '初版', '初期版', 'バーコード',
    ]
    _PKMN_EXCLUDE: list[str] = [
        # later consoles (out of GB/GBC scope)
        'ゲームボーイアドバンス', 'アドバンス', 'advance', 'gba',
        'ニンテンドーds', 'nintendo ds', '3ds', '2ds', 'switch', 'スイッチ',
        'ゲームキューブ', 'gamecube', 'wii', 'vita', 'psp',
        'ニンテンドー64', 'nintendo 64', 'n64', 'スタジアム', 'stadium', 'スナップ', 'snap',
        # non-GB/GBC pokemon game titles (DS/3DS/GBA/Switch + remakes)
        'ハートゴールド', 'ソウルシルバー', 'heartgold', 'soulsilver',
        'ファイアレッド', 'リーフグリーン', 'firered', 'leafgreen',
        'ダイヤモンド', 'パール', 'プラチナ', 'diamond', 'pearl', 'platinum',
        'ブラック', 'ホワイト', 'ルビー', 'サファイア', 'エメラルド', 'emerald',
        'オメガルビー', 'アルファサファイア', 'ウルトラサン', 'ウルトラムーン',
        'バイオレット', 'スカーレット', 'violet', 'scarlet', 'ソード', 'シールド',
        'sword', 'shield', 'アルセウス', 'arceus', 'ブリリアント', 'brilliant',
        'レッツゴー', 'ピカブイ', 'pokopia', 'ぽこ', 'ノブナガ', 'レンジャー', 'ranger',
        'トローゼ', 'trozei', '不思議のダンジョン', 'mystery dungeon', 'conquest',
        # GB-color merch that slips through
        '色紙', 'キーチェーン', 'ペンケース', 'ホッチキス', 'ルービック', 'モンコレ',
        'ソフビ', 'ソフトパック', 'グライダー', 'ポケットピカチュウ', '限定パック', 'キューブ',
        'jukebox', 'ジュークボックス', 'printer', 'プリンター', 'プリンタ',
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
    # Per-color keywords so each GB/GBC mainline game is actually searched
    # (a single keyword requiring ゲームボーイ misses console-less listings).
    _PKMN_UNOPENED_KW: list[str] = [
        'ポケットモンスター 赤 未開封', 'ポケットモンスター 緑 未開封',
        'ポケットモンスター 青 未開封', 'ポケットモンスター ピカチュウ 未開封',
        'ポケットモンスター 金 未開封', 'ポケットモンスター 銀 未開封',
        'ポケットモンスター クリスタル 未開封',
    ]

    # --- Final Fantasy on PlayStation: ONLY FF7 / FF8 / FF9 / FFX ---
    # Titles are matched as FF-qualified tokens so bare digits don't false-match.
    _FF_PS_TITLES: list[str] = [
        'ff7', 'ffvii', 'ファイナルファンタジー7', 'ファイナルファンタジー７',
        'ファイナルファンタジーⅦ', 'ファイナルファンタジーvii', 'final fantasy vii', 'final fantasy 7',
        'ff8', 'ffviii', 'ファイナルファンタジー8', 'ファイナルファンタジー８',
        'ファイナルファンタジーⅧ', 'ファイナルファンタジーviii', 'final fantasy viii', 'final fantasy 8',
        'ff9', 'ffix', 'ファイナルファンタジー9', 'ファイナルファンタジー９',
        'ファイナルファンタジーⅨ', 'ファイナルファンタジーix', 'final fantasy ix', 'final fantasy 9',
        'ff10', 'ffx', 'ffⅹ', 'ファイナルファンタジー10', 'ファイナルファンタジー１０',
        'ファイナルファンタジーⅩ', 'ファイナルファンタジーx', 'final fantasy x', 'final fantasy 10',
    ]
    # PlayStation console (bare 'ps' catches "PS", "PS1", "PS2"; later consoles
    # are stripped by the exclude below so only PS1/PS2 originals survive).
    _FF_PS_MEDIUM: list[str] = ['ps', 'プレイステーション', 'プレステ', 'playstation', 'psx']
    _FF_PS_EXCLUDE: list[str] = [
        # other FF numbers (roman + FFxx forms) -- kills FFX's substring overlap
        'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'ⅺ', 'ⅻ',
        'ff11', 'ff12', 'ff13', 'ff14', 'ff15', 'ff16',
        'ffxi', 'ffxii', 'ffxiii', 'ffxiv', 'ffxv', 'ffxvi',
        # spin-offs / sequels / non-mainline
        'タクティクス', 'tactics', 'ディシディア', 'dissidia', 'クライシス', 'crisis',
        '零式', 'type-0', 'アドベント', 'advent', 'rebirth', 'リバース', 'クロニクル',
        'チョコボ', 'chocobo', 'x-2', 'ⅹ-2', 'ナギ節', '聖剣',
        'ダージュ', 'ケルベロス', 'dirge', 'cerberus', '体験版', 'demo', 'trial',
        # wrong / newer platforms + remasters
        'ps3', 'ps4', 'ps5', 'playstation 3', 'playstation 4', 'playstation 5',
        'psp', 'vita', 'switch', 'スイッチ', 'steam', 'リマスター', 'remaster',
        'リメイク', 'remake', 'ピクセル', 'pixel',
        # merch / media
        '攻略本', 'ガイドブック', '設定資料', 'カレンダー', '非売品', 'バンダナ',
        'サントラ', 'サウンドトラック', 'soundtrack', 'cd', 'dvd', 'フィギュア',
        'ぬいぐるみ', 'カード', 'ステッカー', 'ポスター', 'キーホルダー',
        'プロダクトコード', 'クリアファイル', 'plush', 'figure', 'guide', 'movie',
    ]

    # --- Per-title Famicom/SFC blocks (Castlevania / Chrono Trigger / Metroid /
    # Metal Gear). Each reuses _FC_COND + _FC_EXCLUDE_JP and adds only the
    # sequels/ports that the shared lists don't already reject.
    # Narrower than _FC_MEDIUM: these titles were requested as Famicom (+SFC for
    # Chrono Trigger / Super Metroid), so N64 and Game Boy are NOT accepted —
    # that keeps e.g. "悪魔城ドラキュラ黙示録 ニンテンドウ64" out.
    _FCSFC_MEDIUM: list[str] = [
        'ファミコン', 'ファミリーコンピュータ', 'ファミリーコンピューター',
        'ディスクシステム', 'hvc', 'fcd', 'fc', 'famicom', 'family computer',
        'スーパーファミコン', 'スーファミ', 'super famicom', 'sfc', 'shvc',
        'snes', 'super nintendo',
    ]
    _CASTLEVANIA_EXCLUDE: list[str] = _FC_EXCLUDE_JP + [
        # non-Nintendo ports & later spin-offs that name the franchise
        'pcエンジン', 'pc engine', 'メガドライブ', 'mega drive', 'msx', 'x68000',
        'ワンダースワン', 'wonderswan', 'サターン', 'saturn', 'xbox', 'steam',
        # NOTE: bare "コレクション" is NOT excluded — sellers write "コレクション整理"
        # on genuine sealed listings. Only the re-release collections are named.
        'アニバーサリーコレクション', 'anniversary collection', 'アドヴァンスコレクション',
        'advance collection', 'ドミナスコレクション', 'dominus collection',
        'netflix', 'ネットフリックス',
        'ハーモニー', 'harmony', 'ロードオブシャドウ', 'lords of shadow',
    ]
    _CHRONO_EXCLUDE: list[str] = _FC_EXCLUDE_JP + [
        # different game / later ports (DS, PS1, mobile, Steam all out of scope)
        'クロノクロス', 'クロノ・クロス', 'chrono cross',
        'ラジカルドリーマーズ', 'radical dreamers',
        'アルティメットヒッツ', 'ultimate hits', 'steam', 'アプリ',
    ]
    _METROID_EXCLUDE: list[str] = _FC_EXCLUDE_JP + [
        # sequels / remakes on consoles outside the FC/SFC scope
        'プライム', 'prime', 'ドレッド', 'dread', 'フュージョン', 'fusion',
        'ゼロミッション', 'zero mission', 'サムスリターンズ', 'samus returns',
        'アザーエム', 'other m', 'メトロイド2', 'metroid ii',
    ]
    _METAL_GEAR_EXCLUDE: list[str] = _FC_EXCLUDE_JP + [
        # MGS line and non-Nintendo platforms
        'ソリッド', 'solid', 'mgs', 'サブシスタンス', 'subsistence',
        'ライジング', 'rising', 'サバイヴ', 'survive', 'ファントムペイン',
        'phantom pain', 'ピースウォーカー', 'peace walker',
        'msx', 'メガドライブ', 'xbox', 'steam', 'マスターコレクション',
        'master collection', 'デルタ', 'delta',
    ]

    # --- Kingdom Hearts 1 on PS2 ONLY (incl. Final Mix) ---
    # KH1 listings often read just "キングダムハーツ", so the gate is the title
    # word + a PlayStation term, and every sequel/spin-off/HD collection is
    # rejected explicitly below. Note matching is plain substring, so the
    # sequel numbers are anchored to "ハーツ"/"hearts" (bare "2"/"ii" would
    # false-reject legitimate KH1 titles).
    _KH_TITLES: list[str] = ['キングダムハーツ', 'キングダム ハーツ', 'kingdom hearts']
    _KH_MEDIUM: list[str] = ['ps2', 'ps 2', 'プレイステーション', 'プレステ', 'playstation']
    _KH_EXCLUDE: list[str] = [
        # KH2 and beyond (anchored to the title word so "1" isn't needed)
        'ハーツ2', 'ハーツ２', 'ハーツⅡ', 'ハーツii', 'ハーツ ii', 'ハーツ 2',
        'hearts 2', 'hearts ii', 'kh2', 'kh 2',
        'ハーツ3', 'ハーツ３', 'ハーツⅢ', 'ハーツiii', 'ハーツ 3',
        'hearts 3', 'hearts iii', 'kh3', 'kh 3',
        # spin-offs
        'チェインオブメモリーズ', 'チェイン オブ メモリーズ', 'chain of memories',
        're:コム', 'recom', 're:chain',
        '358', 'デイズ', 'days',
        'バースバイスリープ', 'バース バイ スリープ', 'birth by sleep', 'bbs',
        'リコーデッド', 're:coded', 'コーデッド', 'coded',
        'ドリームドロップ', 'dream drop', 'ddd',
        'メロディオブメモリー', 'melody of memory',
        'アンチェインド', 'unchained', 'ユニオンクロス', 'union', 'ミッシングリンク',
        # HD remasters / collections (PS3/PS4/Switch/Xbox, not the PS2 original)
        'hd 1.5', 'hd1.5', '1.5+', 'hd 2.5', 'hd2.5', '+2.5', 'hd 2.8', 'hd2.8',
        'リミックス', 'remix', 'ザ ストーリー ソー ファー', 'story so far',
        'integrum', 'インテグラム', 'オールインワン', 'all-in-one',
        # wrong platforms
        'ps3', 'ps4', 'ps5', 'playstation 3', 'playstation 4', 'playstation 5',
        'プレイステーション3', 'プレイステーション4', 'プレイステーション5',
        'プレイステーション 3', 'プレイステーション 4', 'プレイステーション 5',
        'psp', 'vita', 'switch', 'スイッチ', 'xbox', 'steam', 'epic',
        'ゲームボーイアドバンス', 'gba', 'ニンテンドーds', '3ds', 'クラウド版',
        'リマスター', 'remaster', 'リメイク', 'remake', '体験版', 'demo', 'trial',
        # merch / media
        '攻略本', 'ガイドブック', '設定資料', 'カレンダー', 'サントラ',
        'サウンドトラック', 'soundtrack', 'cd', 'dvd', 'blu-ray', 'コミック', '漫画',
        'フィギュア', 'figure', 'ぬいぐるみ', 'plush', 'カード', 'トレカ',
        'ステッカー', 'シール', 'ポスター', 'キーホルダー', 'ストラップ',
        'アクリル', 'グッズ', 'クリアファイル', 'プロダクトコード', 'ネックレス',
        'ピアス', 'tシャツ', '空ケース', 'ケースのみ', 'ウエハース', '一番くじ',
        # merch multi-packs that name PS2 but aren't the game
        '種類セット', '全6種', '全5種', '全4種', '全3種', 'コンプリートセット',
    ]

    # --- PlayStation 1 merch/media reject list, shared by the PS1 searches ---
    _PS1_MERCH_EXCLUDE: list[str] = [
        '攻略本', 'ガイドブック', '設定資料', '資料集', 'カレンダー', '冊子',
        'コミック', '漫画', '小説', 'ノベル', '雑誌', 'カタログ', 'チラシ',
        # game magazines that merely name the title on the cover
        '月号', '付録', '増刊', '週刊', '別冊', '電撃playstation',
        '電撃プレイステーション', 'ファミ通', 'ゲーム批評', 'vol.',
        'サントラ', 'サウンドトラック', 'soundtrack', 'cd', 'dvd', 'blu-ray',
        'vhs', 'ビデオ', 'レコード', 'vinyl', '映画', 'movie',
        'フィギュア', 'figure', 'ぬいぐるみ', 'plush', '人形', 'プライズ',
        '一番くじ', 'ガチャ', '缶バッジ', 'バッジ', 'ピンズ', 'メダル',
        'カード', 'トレカ', 'trading card', 'シール', 'ステッカー', 'ポスター',
        'キーホルダー', 'ストラップ', 'アクリル', 'グッズ', 'クリアファイル',
        'tシャツ', 'タオル', 'マグカップ', '時計', 'zippo', 'ライター',
        '空ケース', 'ケースのみ', 'ジャケットのみ', '説明書のみ', 'ディスクのみ',
        'プロダクトコード', 'コントローラ', 'メモリーカード', 'アダプタ',
    ]

    # --- Tekken 1 ONLY (鉄拳, SLPS-00040) on PlayStation ---
    # 鉄拳 is a substring of 鉄拳2/3/4..., so every sequel is rejected by an
    # anchored number. "鉄拳" is also an everyday word (鉄拳制裁) and a comedian's
    # stage name, so the PlayStation gate does the heavy lifting here.
    _TEKKEN1_TITLES: list[str] = ['鉄拳', 'tekken', 'slps-00040', 'slps00040']
    _TEKKEN1_EXCLUDE: list[str] = _PS1_MERCH_EXCLUDE + [
        # sequels (anchored to the title word — bare digits hit prices/codes)
        '鉄拳2', '鉄拳２', '鉄拳3', '鉄拳３', '鉄拳4', '鉄拳４',
        '鉄拳5', '鉄拳５', '鉄拳6', '鉄拳６', '鉄拳7', '鉄拳７', '鉄拳8', '鉄拳８',
        '鉄拳 2', '鉄拳 3', '鉄拳 4', '鉄拳 5', '鉄拳 6', '鉄拳 7', '鉄拳 8',
        'tekken 2', 'tekken 3', 'tekken 4', 'tekken 5', 'tekken 6', 'tekken 7',
        'tekken 8', 'tekken2', 'tekken3', 'tekken ii', 'tekken iii',
        # spin-offs / other product codes for later entries
        'タッグ', 'tag tournament', 'タッグトーナメント', 'ニーナ',
        'デス バイ ディグリーズ', 'death by degrees', 'アドバンス', 'advance',
        'ダークリザレクション', 'dark resurrection', 'ブラッドライン',
        'bloodline', 'ブラッド・ベンジェンス', 'blood vengeance', 'レボリューション',
        'カードチャレンジ', 'モバイル', 'mobile',
        # not the game: the comedian / the idiom
        '鉄拳制裁', 'パラパラ漫画', '振り子',
        # wrong platforms
        'ps2', 'ps3', 'ps4', 'ps5', 'playstation 2', 'playstation 3',
        'playstation 4', 'playstation 5', 'プレイステーション2',
        'プレイステーション3', 'プレイステーション4', 'プレイステーション5',
        'psp', 'vita', 'switch', 'スイッチ', 'xbox', '360', 'steam', 'arcade',
        'アーケード', 'アーカイブス', 'archives', 'gba', 'ニンテンドーds', '3ds',
        'リマスター', 'remaster', 'リメイク', 'remake', '体験版', 'demo', 'trial',
    ]

    # --- Silent Hill 1 ONLY (サイレントヒル) on PlayStation ---
    # Sequel numbers anchored to "ヒル"/"hill"; the 2024 SH2 remake, the HD
    # collection and every spin-off are rejected.
    _SH1_TITLES: list[str] = ['サイレントヒル', 'silent hill', 'silenthill']
    _SH1_EXCLUDE: list[str] = _PS1_MERCH_EXCLUDE + [
        # sequels (anchored to the title word)
        'ヒル2', 'ヒル２', 'ヒル 2', 'ヒルii', 'hill 2', 'hill ii', 'sh2',
        'ヒル3', 'ヒル３', 'ヒル 3', 'ヒルiii', 'hill 3', 'hill iii', 'sh3',
        'ヒル4', 'ヒル４', 'ヒル 4', 'ヒルiv', 'hill 4', 'hill iv', 'sh4',
        'ザ・ルーム', 'ザ ルーム', 'the room',
        # spin-offs / later entries
        'オリジンズ', 'origins', 'ホームカミング', 'homecoming',
        'シャッタードメモリーズ', 'shattered memories', 'ダウンプア', 'downpour',
        'ブックオブメモリーズ', 'book of memories', 'アセンション', 'ascension',
        'サイレントヒルf', 'silent hill f', 'タウンフォール', 'townfall',
        'ショートメッセージ', 'short message', 'pt',
        # collections / remakes / later platforms
        'hdコレクション', 'hd collection', 'hdエディション',
        'リメイク', 'remake', 'リマスター', 'remaster',
        'ps2', 'ps3', 'ps4', 'ps5', 'playstation 2', 'playstation 3',
        'playstation 4', 'playstation 5', 'プレイステーション2',
        'プレイステーション3', 'プレイステーション4', 'プレイステーション5',
        'psp', 'vita', 'switch', 'スイッチ', 'xbox', '360', 'steam',
        'ニンテンドーds', '3ds', 'gba', 'アーカイブス', 'archives',
        # the films
        '映画', 'movie', 'リベレーション', 'revelation', 'blu-ray', 'ブルーレイ',
        '体験版', 'demo', 'trial',
    ]

    # --- Biohazard 1 on PlayStation ONLY (incl. Director's Cut / DualShock ver) ---
    # Sequel numbers are anchored to "ハザード"/"evil" because bare "2"/"3"
    # appear in prices, lot counts and product codes.
    _BIO1_TITLES: list[str] = ['バイオハザード', 'biohazard', 'resident evil', 'bio hazard']
    _BIO1_MEDIUM: list[str] = ['ps', 'プレイステーション', 'プレステ', 'playstation', 'psx']
    _BIO1_EXCLUDE: list[str] = _PS1_MERCH_EXCLUDE + [
        # sequels / numbered entries (anchored to the title word)
        'ハザード2', 'ハザード２', 'ハザードii', 'ハザード 2', 'バイオ2',
        'ハザード3', 'ハザード３', 'ハザードiii', 'ハザード 3', 'バイオ3',
        'ハザード4', 'ハザード４', 'ハザードiv', 'ハザード 4', 'バイオ4',
        'ハザード5', 'ハザード5', 'ハザード6', 'ハザード7', 'ハザード8',
        'ハザード0', 'ハザードゼロ', 'バイオ0',
        'evil 2', 'evil 3', 'evil 4', 'evil 5', 'evil 6', 'evil 7',
        'evil ii', 'evil iii', 'evil zero', 're2', 're3', 're4', 're:2', 're:3',
        # spin-offs
        'ヴェロニカ', 'ベロニカ', 'veronica', 'ガンサバイバー', 'gun survivor',
        'サバイバー', 'survivor', 'アウトブレイク', 'outbreak', 'デッドエイム',
        'dead aim', 'ダークサイド', 'アンブレラ', 'umbrella', 'クロニクルズ',
        'chronicles', 'リベレーションズ', 'revelations', 'ヴィレッジ', 'village',
        'オペレーション', 'operation', 'ラクーンシティ', 'raccoon city',
        'リバースオブジエンド', 'ガイデン', 'gaiden', 'コードベロニカ',
        # remakes / remasters / later platforms
        'リメイク', 'remake', 'リマスター', 'remaster', 'hdリマスター', 'hd remaster',
        'ps2', 'ps3', 'ps4', 'ps5', 'playstation 2', 'playstation 3',
        'playstation 4', 'playstation 5', 'プレイステーション2', 'プレイステーション3',
        'プレイステーション4', 'プレイステーション5', 'psp', 'vita',
        'ゲームキューブ', 'gamecube', 'wii', 'switch', 'スイッチ', 'xbox',
        'steam', 'ニンテンドーds', '3ds', 'アーカイブス', 'archives',
        'ゲームボーイ', 'game boy', 'サターン', 'saturn', 'windows', 'pc版',
        '体験版', 'demo', 'trial', '非売品',
    ]

    # --- Castlevania: Symphony of the Night (悪魔城ドラキュラX 月下の夜想曲) ---
    # PS1 original + the Sega Saturn port; the PSP "Dracula X Chronicle" and
    # every later re-release are rejected. 血の輪廻 (Rondo of Blood) also carries
    # the "ドラキュラX" name, so it is excluded explicitly.
    _SOTN_TITLES: list[str] = [
        '月下の夜想曲', '月下夜想曲', 'symphony of the night', 'sotn', 'gekka',
    ]
    _SOTN_MEDIUM: list[str] = [
        'ps', 'プレイステーション', 'プレステ', 'playstation', 'psx',
        'サターン', 'セガサターン', 'saturn',
    ]
    _SOTN_EXCLUDE: list[str] = _PS1_MERCH_EXCLUDE + [
        # different game that shares the "ドラキュラX" name
        '血の輪廻', 'rondo', 'ロンド', 'pcエンジン', 'pc engine',
        # PSP compilation and later re-releases
        'クロニクル', 'chronicle', 'アドバンスコレクション', 'advance collection',
        'ドミナスコレクション', 'dominus collection', 'レクイエム', 'requiem',
        'アニバーサリーコレクション', 'anniversary collection',
        # wrong platforms
        'ps3', 'ps4', 'ps5', 'playstation 3', 'playstation 4', 'playstation 5',
        'プレイステーション3', 'プレイステーション4', 'プレイステーション5',
        'psp', 'vita', 'switch', 'スイッチ', 'xbox', '360', 'steam',
        'ニンテンドーds', '3ds', 'gba', 'アドバンス', 'アーカイブス', 'archives',
        'スマホ', 'アプリ', 'ios', 'android', '体験版', 'demo', 'trial',
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
            'name': 'Zelda Famicom/SFC/N64 VGA/CGC/Sealed (Mercari)',
            'platform': 'mercari',
            'keywords': ['ゼルダの伝説 ファミコン 未開封', 'ゼルダの伝説 64 未開封', 'ゼルダの伝説 ゲームボーイ 未開封'],
            'state_category': 'mercari_zelda_famicom',
            'validators': [['ゼルダの伝説', 'ゼルダ', 'zelda'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Zelda Famicom/SFC/N64 VGA/CGC/Sealed (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['ゼルダの伝説 ファミコン 未開封', 'ゼルダの伝説 64 未開封', 'ゼルダの伝説 ゲームボーイ 未開封'],
            'state_category': 'yahoo_zelda_famicom',
            'validators': [['ゼルダの伝説', 'ゼルダ', 'zelda'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Zelda Famicom/SFC/N64 VGA/CGC/Sealed (eBay)',
            'platform': 'ebay',
            'keywords': ['zelda famicom', 'zelda nintendo 64', 'zelda game boy'],
            'state_category': 'ebay_zelda_famicom',
            'validators': [['zelda'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_EN,
        },
        # Mario
        {
            'name': 'Mario Famicom/SFC/N64 VGA/CGC/Sealed (Mercari)',
            'platform': 'mercari',
            'keywords': ['スーパーマリオ ファミコン 未開封', 'スーパーマリオ 64 未開封', 'マリオカート 64 未開封', 'スーパーマリオ ゲームボーイ 未開封'],
            'state_category': 'mercari_mario_famicom',
            'validators': [['スーパーマリオ', 'マリオ', 'mario'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Mario Famicom/SFC/N64 VGA/CGC/Sealed (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['スーパーマリオ ファミコン 未開封', 'スーパーマリオ 64 未開封', 'マリオカート 64 未開封', 'スーパーマリオ ゲームボーイ 未開封'],
            'state_category': 'yahoo_mario_famicom',
            'validators': [['スーパーマリオ', 'マリオ', 'mario'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Mario Famicom/SFC/N64 VGA/CGC/Sealed (eBay)',
            'platform': 'ebay',
            'keywords': ['super mario famicom', 'mario nintendo 64', 'mario kart 64', 'super mario game boy'],
            'state_category': 'ebay_mario_famicom',
            'validators': [['mario'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_EN,
        },
        # Dragon Quest
        {
            'name': 'Dragon Quest Famicom/SFC/N64 VGA/CGC/Sealed (Mercari)',
            'platform': 'mercari',
            'keywords': ['ドラゴンクエスト ファミコン 未開封', 'ドラゴンクエスト 64 未開封', 'ドラゴンクエスト ゲームボーイ 未開封'],
            'state_category': 'mercari_dq_famicom',
            'validators': [['ドラゴンクエスト', 'ドラクエ', 'dragon quest'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Dragon Quest Famicom/SFC/N64 VGA/CGC/Sealed (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['ドラゴンクエスト ファミコン 未開封', 'ドラゴンクエスト 64 未開封', 'ドラゴンクエスト ゲームボーイ 未開封'],
            'state_category': 'yahoo_dq_famicom',
            'validators': [['ドラゴンクエスト', 'ドラクエ', 'dragon quest'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Dragon Quest Famicom/SFC/N64 VGA/CGC/Sealed (eBay)',
            'platform': 'ebay',
            'keywords': ['dragon quest famicom', 'dragon quest nintendo 64', 'dragon quest game boy'],
            'state_category': 'ebay_dq_famicom',
            'validators': [['dragon quest', 'dragon warrior'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_EN,
        },
        # Final Fantasy
        {
            'name': 'Final Fantasy Famicom/SFC/N64 VGA/CGC/Sealed (Mercari)',
            'platform': 'mercari',
            'keywords': ['ファイナルファンタジー ファミコン 未開封', 'ファイナルファンタジー 64 未開封', 'ファイナルファンタジー ゲームボーイ 未開封'],
            'state_category': 'mercari_ff_famicom',
            'validators': [['ファイナルファンタジー', 'final fantasy'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Final Fantasy Famicom/SFC/N64 VGA/CGC/Sealed (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['ファイナルファンタジー ファミコン 未開封', 'ファイナルファンタジー 64 未開封', 'ファイナルファンタジー ゲームボーイ 未開封'],
            'state_category': 'yahoo_ff_famicom',
            'validators': [['ファイナルファンタジー', 'final fantasy'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_JP,
        },
        {
            'name': 'Final Fantasy Famicom/SFC/N64 VGA/CGC/Sealed (eBay)',
            'platform': 'ebay',
            'keywords': ['final fantasy famicom', 'final fantasy nintendo 64', 'final fantasy game boy'],
            'state_category': 'ebay_ff_famicom',
            'validators': [['final fantasy'], _FC_MEDIUM, _FC_COND],
            'exclude': _FC_EXCLUDE_EN,
        },
        # --- Pokemon games, unopened (未開封) — game-medium gated ---
        # Mercari only: NO sealed-word validator. Mercari's keyword search
        # matches title AND description, and every _PKMN_UNOPENED_KW already
        # contains 未開封 — so anything returned here has already been filtered
        # on sealed-ness. Re-checking the title would drop listings where the
        # seller states 未開封 only in the description and leads the title with
        # the variant name, e.g. m65338075020 "限定品 トヨタ限定 ポケットモンスター
        # 青 ゲームボーイソフト" (Toyota-limited Blue) — exactly the rare promos
        # worth catching. Trade-off: looser description matches get through;
        # _PKMN_EXCLUDE + _PKMN_GAME still gate out merch and non-GB/GBC games.
        {
            'name': 'Pokemon Game Unopened (Mercari)',
            'platform': 'mercari',
            'keywords': _PKMN_UNOPENED_KW,
            'state_category': 'mercari_pokemon_unopened',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                _PKMN_GAME,
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        {
            'name': 'Pokemon Game Unopened (Yahoo)',
            'platform': 'yahoo',
            'keywords': _PKMN_UNOPENED_KW,
            'state_category': 'yahoo_pokemon_unopened',
            'validators': [
                ['ポケモン', 'ポケットモンスター', 'pocket monster'],
                _PKMN_GAME,
                ['未開封', '未使用', 'sealed', 'unopened'],
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        {
            'name': 'Pokemon Game Unopened (eBay)',
            'platform': 'ebay',
            'keywords': [
                'pokemon red game boy sealed', 'pokemon green game boy sealed',
                'pokemon blue game boy sealed', 'pokemon yellow game boy sealed',
                'pokemon gold game boy sealed', 'pokemon silver game boy sealed',
                'pokemon crystal game boy sealed',
            ],
            'state_category': 'ebay_pokemon_unopened',
            'validators': [
                ['pocket monster', 'pokemon', 'pokémon'],
                _PKMN_GAME,
                ['sealed', 'unopened', '未開封'],
            ],
            'exclude': _PKMN_EXCLUDE,
        },
        # --- Final Fantasy PlayStation (FF7/8/9/X only), sealed/graded ---
        {
            'name': 'Final Fantasy PS VII-X Sealed/Graded (Mercari)',
            'platform': 'mercari',
            'keyword': 'ファイナルファンタジー プレイステーション 未開封',
            'state_category': 'mercari_ff_ps',
            'validators': [_FF_PS_TITLES, _FF_PS_MEDIUM, _FC_COND],
            'exclude': _FF_PS_EXCLUDE,
        },
        {
            'name': 'Final Fantasy PS VII-X Sealed/Graded (Yahoo)',
            'platform': 'yahoo',
            'keyword': 'ファイナルファンタジー プレイステーション 未開封',
            'state_category': 'yahoo_ff_ps',
            'validators': [_FF_PS_TITLES, _FF_PS_MEDIUM, _FC_COND],
            'exclude': _FF_PS_EXCLUDE,
        },
        {
            'name': 'Final Fantasy PS VII-X Sealed/Graded (eBay)',
            'platform': 'ebay',
            'keyword': 'final fantasy playstation sealed',
            'state_category': 'ebay_ff_ps',
            'validators': [_FF_PS_TITLES, _FF_PS_MEDIUM, _FC_COND],
            'exclude': _FF_PS_EXCLUDE,
        },
        # --- Castlevania Famicom (悪魔城ドラキュラ), sealed/graded ---
        {
            'name': 'Castlevania Famicom Sealed/Graded (Mercari)',
            'platform': 'mercari',
            'keywords': ['悪魔城ドラキュラ ファミコン 未開封', '悪魔城ドラキュラ ディスクシステム 未開封'],
            'state_category': 'mercari_castlevania_famicom',
            'validators': [['悪魔城ドラキュラ', '悪魔城', 'castlevania', 'akumajo', 'akumajou'], _FCSFC_MEDIUM, _FC_COND],
            'exclude': _CASTLEVANIA_EXCLUDE,
        },
        {
            'name': 'Castlevania Famicom Sealed/Graded (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['悪魔城ドラキュラ ファミコン 未開封', '悪魔城ドラキュラ ディスクシステム 未開封'],
            'state_category': 'yahoo_castlevania_famicom',
            'validators': [['悪魔城ドラキュラ', '悪魔城', 'castlevania', 'akumajo', 'akumajou'], _FCSFC_MEDIUM, _FC_COND],
            'exclude': _CASTLEVANIA_EXCLUDE,
        },
        # --- Chrono Trigger Super Famicom, sealed/graded ---
        {
            'name': 'Chrono Trigger SFC Sealed/Graded (Mercari)',
            'platform': 'mercari',
            'keywords': ['クロノトリガー スーパーファミコン 未開封', 'クロノ・トリガー SFC 未開封'],
            'state_category': 'mercari_chrono_trigger_sfc',
            'validators': [
                ['クロノトリガー', 'クロノ・トリガー', 'クロノ トリガー', 'chrono trigger'],
                _FCSFC_MEDIUM,
                _FC_COND,
            ],
            'exclude': _CHRONO_EXCLUDE,
        },
        {
            'name': 'Chrono Trigger SFC Sealed/Graded (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['クロノトリガー スーパーファミコン 未開封', 'クロノ・トリガー SFC 未開封'],
            'state_category': 'yahoo_chrono_trigger_sfc',
            'validators': [
                ['クロノトリガー', 'クロノ・トリガー', 'クロノ トリガー', 'chrono trigger'],
                _FCSFC_MEDIUM,
                _FC_COND,
            ],
            'exclude': _CHRONO_EXCLUDE,
        },
        # --- Kingdom Hearts 1 (PS2 only, incl. Final Mix), sealed/graded ---
        {
            'name': 'Kingdom Hearts 1 PS2 Sealed/Graded (Mercari)',
            'platform': 'mercari',
            'keywords': ['キングダムハーツ PS2 未開封', 'キングダムハーツ1 未開封', 'キングダムハーツ ファイナルミックス 未開封'],
            'state_category': 'mercari_kh1_ps2',
            'validators': [_KH_TITLES, _KH_MEDIUM, _FC_COND],
            'exclude': _KH_EXCLUDE,
        },
        {
            'name': 'Kingdom Hearts 1 PS2 Sealed/Graded (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['キングダムハーツ PS2 未開封', 'キングダムハーツ1 未開封', 'キングダムハーツ ファイナルミックス 未開封'],
            'state_category': 'yahoo_kh1_ps2',
            'validators': [_KH_TITLES, _KH_MEDIUM, _FC_COND],
            'exclude': _KH_EXCLUDE,
        },
        # --- Metroid Famicom (メトロイド), sealed/graded ---
        {
            'name': 'Metroid Famicom Sealed/Graded (Mercari)',
            'platform': 'mercari',
            'keywords': ['メトロイド ファミコン 未開封', 'メトロイド ディスクシステム 未開封'],
            'state_category': 'mercari_metroid_famicom',
            'validators': [['メトロイド', 'metroid'], _FCSFC_MEDIUM, _FC_COND],
            'exclude': _METROID_EXCLUDE,
        },
        {
            'name': 'Metroid Famicom Sealed/Graded (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['メトロイド ファミコン 未開封', 'メトロイド ディスクシステム 未開封'],
            'state_category': 'yahoo_metroid_famicom',
            'validators': [['メトロイド', 'metroid'], _FCSFC_MEDIUM, _FC_COND],
            'exclude': _METROID_EXCLUDE,
        },
        # --- Metal Gear Famicom (メタルギア), sealed/graded ---
        {
            'name': 'Metal Gear Famicom Sealed/Graded (Mercari)',
            'platform': 'mercari',
            'keywords': ['メタルギア ファミコン 未開封'],
            'state_category': 'mercari_metal_gear_famicom',
            'validators': [['メタルギア', 'metal gear'], _FCSFC_MEDIUM, _FC_COND],
            'exclude': _METAL_GEAR_EXCLUDE,
        },
        {
            'name': 'Metal Gear Famicom Sealed/Graded (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['メタルギア ファミコン 未開封'],
            'state_category': 'yahoo_metal_gear_famicom',
            'validators': [['メタルギア', 'metal gear'], _FCSFC_MEDIUM, _FC_COND],
            'exclude': _METAL_GEAR_EXCLUDE,
        },
        # --- Biohazard 1 (PlayStation), sealed/graded ---
        {
            'name': 'Biohazard 1 PS Sealed/Graded (Mercari)',
            'platform': 'mercari',
            'keywords': ['バイオハザード プレイステーション 未開封', 'バイオハザード PS 未開封'],
            'state_category': 'mercari_biohazard1_ps',
            'validators': [_BIO1_TITLES, _BIO1_MEDIUM, _FC_COND],
            'exclude': _BIO1_EXCLUDE,
        },
        {
            'name': 'Biohazard 1 PS Sealed/Graded (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['バイオハザード プレイステーション 未開封', 'バイオハザード PS 未開封'],
            'state_category': 'yahoo_biohazard1_ps',
            'validators': [_BIO1_TITLES, _BIO1_MEDIUM, _FC_COND],
            'exclude': _BIO1_EXCLUDE,
        },
        # --- Castlevania: Symphony of the Night (月下の夜想曲), sealed/graded ---
        {
            'name': 'Castlevania Symphony of the Night Sealed/Graded (Mercari)',
            'platform': 'mercari',
            'keywords': ['月下の夜想曲 未開封', '悪魔城ドラキュラX 月下の夜想曲 未開封'],
            'state_category': 'mercari_sotn',
            'validators': [_SOTN_TITLES, _SOTN_MEDIUM, _FC_COND],
            'exclude': _SOTN_EXCLUDE,
        },
        {
            'name': 'Castlevania Symphony of the Night Sealed/Graded (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['月下の夜想曲 未開封', '悪魔城ドラキュラX 月下の夜想曲 未開封'],
            'state_category': 'yahoo_sotn',
            'validators': [_SOTN_TITLES, _SOTN_MEDIUM, _FC_COND],
            'exclude': _SOTN_EXCLUDE,
        },
        # --- Tekken 1 only (鉄拳 / SLPS-00040, PlayStation), sealed/graded ---
        {
            'name': 'Tekken 1 PS Sealed/Graded (Mercari)',
            'platform': 'mercari',
            'keywords': ['鉄拳 プレイステーション 未開封', '鉄拳 PS1 未開封'],
            'state_category': 'mercari_tekken1_ps',
            'validators': [_TEKKEN1_TITLES, _BIO1_MEDIUM, _FC_COND],
            'exclude': _TEKKEN1_EXCLUDE,
        },
        {
            'name': 'Tekken 1 PS Sealed/Graded (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['鉄拳 プレイステーション 未開封', '鉄拳 PS1 未開封'],
            'state_category': 'yahoo_tekken1_ps',
            'validators': [_TEKKEN1_TITLES, _BIO1_MEDIUM, _FC_COND],
            'exclude': _TEKKEN1_EXCLUDE,
        },
        # --- Silent Hill 1 only (サイレントヒル, PlayStation), sealed/graded ---
        {
            'name': 'Silent Hill 1 PS Sealed/Graded (Mercari)',
            'platform': 'mercari',
            'keywords': ['サイレントヒル 未開封', 'サイレントヒル プレイステーション 未開封'],
            'state_category': 'mercari_silenthill1_ps',
            'validators': [_SH1_TITLES, _BIO1_MEDIUM, _FC_COND],
            'exclude': _SH1_EXCLUDE,
        },
        {
            'name': 'Silent Hill 1 PS Sealed/Graded (Yahoo)',
            'platform': 'yahoo',
            'keywords': ['サイレントヒル 未開封', 'サイレントヒル プレイステーション 未開封'],
            'state_category': 'yahoo_silenthill1_ps',
            'validators': [_SH1_TITLES, _BIO1_MEDIUM, _FC_COND],
            'exclude': _SH1_EXCLUDE,
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

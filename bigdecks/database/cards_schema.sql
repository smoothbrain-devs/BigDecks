CREATE TABLE IF NOT EXISTS core (
    id INTEGER PRIMARY KEY,
    scryfall_id TEXT NOT NULL,
    arena_id INTEGER,
    mtgo_id INTEGER,
    mtgo_foil_id INTEGER,
    multiverse_ids TEXT,  -- JSON Array of ints.
    layout TEXT NOT NULL,
    oracle_id TEXT,
    rulings_uri TEXT,
    scryfall_uri TEXT,  -- Link to scryfall page for the card.
    uri TEXT,  -- Link to download the card object from scryfall api.
    all_parts BOOLEAN NOT NULL, -- If true, corresponding entries in all_parts table.
    card_faces BOOLEAN NOT NULL,  -- If true, corresponding entries in card_faces table.
    cmc REAL NOT NULL,
    color_identity TEXT NOT NULL,  -- JSON Colors array (strings or empty).
    color_indicator TEXT,  -- JSON Colors array.
    colors TEXT,  -- JSON Colors array.
    defense TEXT,
    game_changer BOOLEAN,
    hand_modifier TEXT,
    keywords TEXT NOT NULL,  -- JSON Array of strings.
    -- Format legalities (legal, not_legal, restricted, banned) --
    standard TEXT NOT NULL,
    future TEXT NOT NULL,
    historic TEXT NOT NULL,
    timeless TEXT NOT NULL,
    gladiator TEXT NOT NULL,
    pioneer TEXT NOT NULL,
    explorer TEXT NOT NULL,
    modern TEXT NOT NULL,
    legacy TEXT NOT NULL,
    pauper TEXT NOT NULL,
    vintage TEXT NOT NULL,
    penny TEXT NOT NULL,
    commander TEXT NOT NULL,
    oathbreaker TEXT NOT NULL,
    standardbrawl TEXT NOT NULL,
    brawl TEXT NOT NULL,
    alchemy TEXT NOT NULL,
    paupercommander TEXT NOT NULL,
    duel TEXT NOT NULL,
    oldschool TEXT NOT NULL,
    premodern TEXT NOT NULL,
    predh TEXT NOT NULL,
    -- end Format legalities --
    life_modifier TEXT,
    loyalty TEXT,
    mana_cost TEXT,
    name NOT NULL,
    oracle_text TEXT,
    power TEXT,
    produced_mana TEXT, -- JSON Colors array,
    reserved BOOLEAN NOT NULL,
    toughness TEXT,
    type_line TEXT NOT NULL,
    supertype TEXT, -- JSON Array of strings. (May only be 1)
    cardtype TEXT, -- JSON Array of strings. (May only be 1)
    subtype TEXT,  -- JSON Array of strings. (May only be 1)
    artist TEXT,
    artist_ids TEXT,  -- JSON Array of strings.
    attraction_lights TEXT,  -- JSON Array of strings.
    booster BOOLEAN NOT NULL,
    border_color TEXT NOT NULL,
    card_back_id TEXT NOT NULL,
    collector_number TEXT NOT NULL,
    content_warning BOOLEAN, -- True if you should avoid using this print.
    digital BOOLEAN NOT NULL,
    -- Finishes --
    foil BOOLEAN NOT NULL,
    nonfoil BOOLEAN NOT NULL,
    etched BOOLEAN NOT NULL,
    -- end Finishes --
    flavor_name TEXT,  -- e.g. Godzilla card names
    flavor_text TEXT,
    frame_effects TEXT,  -- JSON Array of strings.
    frame TEXT NOT NULL,
    full_art BOOLEAN,
    -- Available in --
    paper BOOLEAN NOT NULL,
    arena BOOLEAN NOT NULL,
    mtgo BOOLEAN NOT NULL,
    -- End Available --
    highres_image BOOLEAN NOT NULL,
    illustration_id TEXT,
    image_status TEXT,
    -- Image uris --
    png TEXT,
    border_crop TEXT,
    art_crop TEXT,
    large TEXT,
    normal TEXT,
    small TEXT,
    -- end Image URIS --
    oversized BOOLEAN NOT NULL,
    -- Prices --
    price_usd TEXT,
    price_usd_foil TEXT,
    price_usd_etched TEXT,
    price_eur TEXT,
    price_eur_foil TEXT,
    price_eur_etched TEXT,
    price_tix TEXT,
    -- end Prices --
    printed_name TEXT,
    printed_text TEXT,
    printed_type_line TEXT,
    promo BOOLEAN,
    promo_types TEXT,  -- JSON Array of strings.
    rarity TEXT NOT NULL,
    released_at TEXT NOT NULL,
    reprint BOOLEAN NOT NULL,
    scryfall_set_uri TEXT NOT NULL,
    set_name TEXT NOT NULL,  -- Full set name
    set_search_uri TEXT NOT NULL,  -- Link to set on Scryfall
    set_type TEXT NOT NULL,  -- (e.g. expansion)
    set_uri TEXT NOT NULL,  -- link to card's set object on Scryfall API.
    set_code TEXT NOT NULL,
    set_id TEXT NOT NULL,  -- Set object UUID
    story_spotlight BOOLEAN NOT NULL,
    textless BOOLEAN NOT NULL,
    variation BOOLEAN NOT NULL,
    variation_of TEXT,  -- printing id of printing this card is a variation of.
    security_stamp TEXT,
    watermark TEXT
);


CREATE TABLE IF NOT EXISTS all_parts (
    id INTEGER PRIMARY KEY,
    core_id TEXT NOT NULL, -- Scryfall id for parent card
    scryfall_id TEXT NOT NULL,  -- Scryfall id for this card
    component TEXT NOT NULL,  -- What role this card plays in the relationship (e.g. token)
    name TEXT NOT NULL,
    type_line TEXT NOT NULL,
    supertype TEXT, -- JSON Array of strings. (May only be 1)
    cardtype TEXT, -- JSON Array of strings. (May only be 1)
    subtype TEXT, -- JSON Array of strings. (May only be 1)
    uri TEXT NOT NULL,  -- URI for card object
    FOREIGN KEY(core_id) REFERENCES core(scryfall_id)
);


CREATE TABLE IF NOT EXISTS card_faces (
    id INTEGER PRIMARY KEY,
    core_id TEXT NOT NULL,
    artist_id TEXT,
    cmc REAL,
    color_indicator TEXT,
    colors TEXT,
    defense TEXT,
    flavor_text TEXT,
    illustration_id TEXT,
    -- Image URIS --
    png TEXT,
    border_crop TEXT,
    art_crop TEXT,
    large TEXT,
    normal TEXT,
    small TEXT,
    -- end Image URIS --
    layout TEXT,
    loyalty TEXT,
    mana_cost TEXT NOT NULL,
    name TEXT NOT NULL,
    oracle_id TEXT,
    oracle_text TEXT,
    power TEXT,
    printed_name TEXT,  -- Localized name
    printed_text TEXT,  -- Localized text
    printed_type_line TEXT,  -- Localized type line
    toughness TEXT,
    type_line TEXT,
    supertype TEXT, -- JSON Array of strings. (May only be 1)
    cardtype TEXT, -- JSON Array of strings. (May only be 1)
    subtype TEXT, -- JSON Array of strings. (May only be 1)
    watermark TEXT,
    FOREIGN KEY(core_id) REFERENCES core(scryfall_id)
);

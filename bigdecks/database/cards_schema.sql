CREATE TABLE IF NOT EXISTS core (
    id INTEGER PRIMARY KEY,
    scryfall_id TEXT,
    arena_id INTEGER,
    mtgo_id INTEGER,
    mtgo_foil_id INTEGER,
    layout TEXT NOT NULL,
    all_parts TEXT,  -- JSON array with Related Card Objects if exists.
    card_faces TEXT,  -- JSON array with Card Face Objects if exists.
    cmc REAL NOT NULL,
    color_identity TEXT NOT NULL,
    colors TEXT,
    defense TEXT,
    game_changer BOOLEAN,
    hand_modifier TEXT,
    keywords TEXT,  -- JSON array with keywords the card uses.
    legalities TEXT NOT NULL,  -- JSON object with the legality of the card int different formats.
    life_modifier TEXT,
    loyalty TEXT,
    mana_cost TEXT,
    name TEXT NOT NULL,
    oracle_text TEXT,
    power TEXT,
    produced_mana TEXT,
    reserved BOOLEAN NOT NULL,
    toughness TEXT,
    type_line TEXT NOT NULL,
    collector_number TEXT,
    digital BOOLEAN NOT NULL,
    flavor_name TEXT,
    flavor_text TEXT,
    full_art BOOLEAN NOT NULL,
    games TEXT NOT NULL,  -- JSON array of games the card print is available in.
    highres_image BOOLEAN NOT NULL,
    image_uris TEXT,  -- JSON Object listing available imagery for the card.
    oversized BOOLEAN NOT NULL,
    prices_usd TEXT,
    prices_usd_foil TEXT,
    prices_usd_etched TEXT,
    prices_tix TEXT,
    rarity TEXT NOT NULL,
    reprint BOOLEAN NOT NULL,
    set_name TEXT NOT NULL,
    set TEXT NOT NULL,
    variation BOOLEAN NOT NULL,
    variation_of TEXT
);

CREATE TABLE IF NOT EXISTS faces (
    id INTEGER PRIMARY KEY,
    name TEXT ,
    scryfall_id TEXT NOT NULL,
    cmc REAL NOT NULL,
    colors TEXT,
    defense TEXT,
    image_uris TEXT,  -- JSON Object listing available imagery for the card.
    layout TEXT,
    loyalty TEXT,
    mana_cost TEXT NOT NULL,
    oracle_text TEXT,
    power TEXT,
    toughness TEXT,
    type_line TEXT,
    FOREIGN KEY(id) REFERENCES core(id)
);

-- Tournament table
CREATE TABLE IF NOT EXISTS tournament (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  format TEXT NOT NULL,
  date TEXT NOT NULL,  -- ISO format date string
  max_players INTEGER NOT NULL,
  status TEXT NOT NULL,  -- 'registration', 'in_progress', 'completed'
  organizer_id INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organizer_id) REFERENCES user (id)
);

-- Participant table to track tournament registrations
CREATE TABLE IF NOT EXISTS participant (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tournament_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status TEXT NOT NULL,  -- 'registered', 'dropped', 'disqualified'
  FOREIGN KEY (tournament_id) REFERENCES tournament (id),
  FOREIGN KEY (user_id) REFERENCES user (id),
  UNIQUE (tournament_id, user_id)
);

-- Match table to track pairings and results
CREATE TABLE IF NOT EXISTS match (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tournament_id INTEGER NOT NULL,
  round INTEGER NOT NULL,
  player1_id INTEGER NOT NULL,
  player2_id INTEGER NOT NULL,
  player1_wins INTEGER DEFAULT 0,
  player2_wins INTEGER DEFAULT 0,
  draws INTEGER DEFAULT 0,
  status TEXT NOT NULL,  -- 'pending', 'in_progress', 'completed'
  result_reported_by INTEGER,  -- user_id of who reported the result
  FOREIGN KEY (tournament_id) REFERENCES tournament (id),
  FOREIGN KEY (player1_id) REFERENCES participant (id),
  FOREIGN KEY (player2_id) REFERENCES participant (id),
  FOREIGN KEY (result_reported_by) REFERENCES user (id)
);

-- Standing table to track player standings in a tournament
CREATE TABLE IF NOT EXISTS standing (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tournament_id INTEGER NOT NULL,
  participant_id INTEGER NOT NULL,
  points INTEGER DEFAULT 0,
  matches_played INTEGER DEFAULT 0,
  matches_won INTEGER DEFAULT 0,
  matches_lost INTEGER DEFAULT 0,
  matches_drawn INTEGER DEFAULT 0,
  game_win_percentage REAL DEFAULT 0,
  opponent_match_win_percentage REAL DEFAULT 0,  -- For tiebreakers
  FOREIGN KEY (tournament_id) REFERENCES tournament (id),
  FOREIGN KEY (participant_id) REFERENCES participant (id),
  UNIQUE (tournament_id, participant_id)
);
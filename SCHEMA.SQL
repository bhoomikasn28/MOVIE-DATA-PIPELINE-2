

CREATE TABLE IF NOT EXISTS movies (
    movie_id      INTEGER PRIMARY KEY,
    title         TEXT NOT NULL,
    release_year  INTEGER,
    genres_raw    TEXT NOT NULL,
    director      TEXT,
    writer        TEXT,
    actors        TEXT,
    plot          TEXT,
    language      TEXT,
    country       TEXT,
    awards        TEXT,
    imdb_rating   REAL,
    imdb_votes    INTEGER,
    imdb_id       TEXT,
    UNIQUE(movie_id)
);

CREATE TABLE IF NOT EXISTS genres (
    genre_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id   INTEGER NOT NULL,
    genre_id   INTEGER NOT NULL,
    PRIMARY KEY (movie_id, genre_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ratings (
    user_id    INTEGER NOT NULL,
    movie_id   INTEGER NOT NULL,
    rating     REAL    NOT NULL,
    ts_utc     INTEGER NOT NULL,
    PRIMARY KEY (user_id, movie_id, ts_utc),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ratings_movie ON ratings(movie_id);
CREATE INDEX IF NOT EXISTS idx_ratings_user  ON ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_movies_year   ON movies(release_year);

# etl.py
# Movie Data Pipeline: MovieLens + OMDb -> SQLiteS

import os, re, json, time, argparse, sqlite3, logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import pandas as pd, requests

# -------------------------------
# 1️⃣ Setup and Configuration
# -------------------------------
# Load environment variables (for OMDb API key)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

OMDB_API_KEY = (os.environ.get("OMDB_API_KEY") or "").strip()
OMDB_BASE = "http://www.omdbapi.com/"
TITLE_YEAR_PATTERN = re.compile(r"\s*\((\d{4})\)\s*$")
CACHE_FILE = Path("omdb_cache.json")

# -------------------------------
# Helper Functions
# -------------------------------

def ensure_db(conn: sqlite3.Connection, schema_path: str):
    """Create database tables if schema.sql exists."""
    conn.execute("PRAGMA foreign_keys = ON;")
    if schema_path and Path(schema_path).exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

def parse_title_and_year(raw_title: str):
    """Extract clean title and year from MovieLens titles."""
    if not isinstance(raw_title, str):
        return str(raw_title), None
    m = TITLE_YEAR_PATTERN.search(raw_title)
    if m:
        year = int(m.group(1))
        clean_title = TITLE_YEAR_PATTERN.sub("", raw_title).strip()
        return clean_title, year
    return raw_title, None

def load_cache():
    """Load cached OMDb responses from JSON."""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_cache(cache):
    """Save updated OMDb cache to file."""
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

def omdb_lookup(title: str, year: Optional[int]):
    """Fetch additional movie details from OMDb API."""
    if not OMDB_API_KEY:
        return None
    params = {"t": title, "apikey": OMDB_API_KEY}
    if year:
        params["y"] = str(year)
    try:
        r = requests.get(OMDB_BASE, params=params, timeout=15)
        if r.status_code == 200 and r.json().get("Response") == "True":
            return r.json()
        # Retry without year if no match found
        if year:
            params.pop("y", None)
            r = requests.get(OMDB_BASE, params=params, timeout=15)
            if r.status_code == 200 and r.json().get("Response") == "True":
                return r.json()
    except Exception:
        return None
    return None

def coerce_int(x):
    """Convert string number to integer safely."""
    try:
        return int(str(x).replace(",", "").strip())
    except Exception:
        return None

# -------------------------------
# 2️⃣ Main ETL Process
# -------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--movies", default="data/movies.csv")
    ap.add_argument("--ratings", default="data/ratings.csv")
    ap.add_argument("--db", default="movies.db")
    ap.add_argument("--schema", default="schema.sql")
    ap.add_argument("--rate-limit-ms", type=int, default=250)
    ap.add_argument("--omdb-limit", type=int, default=None)
    args = ap.parse_args()

    # -------------------------------
    # 🟩 EXTRACT
    # -------------------------------
    # Load MovieLens datasets (movies and ratings)
    conn = sqlite3.connect(args.db)
    ensure_db(conn, args.schema)

    movies_df = pd.read_csv(args.movies)
    ratings_df = pd.read_csv(args.ratings)

    # Rename columns for consistency
    movies_df = movies_df.rename(columns={"movieId": "movie_id", "title": "title", "genres": "genres_raw"})
    ratings_df = ratings_df.rename(columns={"userId": "user_id", "movieId": "movie_id", "rating": "rating", "timestamp": "ts_utc"})

    # -------------------------------
    # 🟨 TRANSFORM
    # -------------------------------
    cache = load_cache()
    lookups_done = 0

    # Loop through each movie to clean titles and enrich with OMDb data
    for _, row in movies_df.iterrows():
        movie_id = int(row["movie_id"])
        raw_title = str(row["title"])
        genres_raw = str(row["genres_raw"]) if pd.notna(row["genres_raw"]) else ""
        clean_title, inferred_year = parse_title_and_year(raw_title)

        omdb = {}
        if OMDB_API_KEY:
            key = f"{clean_title}|{inferred_year or ''}"
            omdb = cache.get(key, {})
            if not omdb and (args.omdb_limit is None or lookups_done < args.omdb_limit):
                omdb = omdb_lookup(clean_title, inferred_year) or {}
                cache[key] = omdb
                save_cache(cache)
                lookups_done += 1
                if args.rate_limit_ms > 0:
                    time.sleep(args.rate_limit_ms / 1000.0)

        # Convert IMDb rating if available
        imdb_rating = None
        try:
            ir = omdb.get("imdbRating")
            if ir not in (None, "N/A"):
                imdb_rating = float(ir)
        except Exception:
            imdb_rating = None

        # -------------------------------
        # 🟦 LOAD (MOVIES TABLE)
        # -------------------------------
        # Insert or update movie details into the movies table
        conn.execute(
            """
            INSERT INTO movies (
                movie_id, title, release_year, genres_raw,
                director, writer, actors, plot, language, country, awards,
                imdb_rating, imdb_votes, imdb_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(movie_id) DO UPDATE SET
                title=excluded.title,
                release_year=excluded.release_year,
                genres_raw=excluded.genres_raw,
                director=excluded.director,
                writer=excluded.writer,
                actors=excluded.actors,
                plot=excluded.plot,
                language=excluded.language,
                country=excluded.country,
                awards=excluded.awards,
                imdb_rating=excluded.imdb_rating,
                imdb_votes=excluded.imdb_votes,
                imdb_id=excluded.imdb_id;
            """,
            (
                movie_id,
                clean_title,
                inferred_year or (int(omdb.get("Year")) if (omdb.get("Year") and str(omdb.get("Year")).isdigit()) else None),
                genres_raw,
                omdb.get("Director"),
                omdb.get("Writer"),
                omdb.get("Actors"),
                omdb.get("Plot"),
                omdb.get("Language"),
                omdb.get("Country"),
                omdb.get("Awards"),
                imdb_rating,
                coerce_int(omdb.get("imdbVotes")) if omdb.get("imdbVotes") not in (None, "N/A") else None,
                omdb.get("imdbID"),
            ),
        )

        # Normalize and link genres
        if genres_raw:
            for g in genres_raw.split("|"):
                g = g.strip()
                if not g or g == "(no genres listed)":
                    continue
                conn.execute("INSERT INTO genres(name) VALUES (?) ON CONFLICT(name) DO NOTHING;", (g,))
                gid = conn.execute("SELECT genre_id FROM genres WHERE name = ?;", (g,)).fetchone()[0]
                conn.execute("INSERT OR IGNORE INTO movie_genres(movie_id, genre_id) VALUES (?, ?);", (movie_id, gid))

    # -------------------------------
    # 🟦 LOAD (RATINGS TABLE)
    # -------------------------------
    # Insert or update user ratings
    ratings_df["user_id"] = ratings_df["user_id"].astype(int)
    ratings_df["movie_id"] = ratings_df["movie_id"].astype(int)
    ratings_df["rating"] = ratings_df["rating"].astype(float)
    ratings_df["ts_utc"] = ratings_df["ts_utc"].astype(int)

    for _, r in ratings_df.iterrows():
        conn.execute(
            """
            INSERT INTO ratings (user_id, movie_id, rating, ts_utc)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, movie_id, ts_utc) DO UPDATE SET rating=excluded.rating;
            """,
            (int(r["user_id"]), int(r["movie_id"]), float(r["rating"]), int(r["ts_utc"])),
        )

    # Commit and close database
    conn.commit()
    conn.close()
    print("✅ ETL Completed Successfully! movies.db is ready.")

# -------------------------------
# Run the script
# -------------------------------
if __name__ == "__main__":
    main()

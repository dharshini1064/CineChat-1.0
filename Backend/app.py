from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

# ✅ Your actual API keys
GEMINI_API_KEY = "AIzaSyBqpiVebxz4nVz3re7MN1avq-kx6qrHBeg"
TMDB_API_KEY = "8e2d9acdba2afa99e751607fbb17535e"

# 🎭 Genre mapping for TMDb
GENRE_MAPPING = {
    "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
    "crime": 80, "documentary": 99, "drama": 18, "family": 10751,
    "fantasy": 14, "history": 36, "horror": 27, "music": 10402,
    "mystery": 9648, "romance": 10749, "science fiction": 878,
    "tv movie": 10770, "thriller": 53, "war": 10752, "western": 37
}

# Synonyms and partials for genre fallback
GENRE_SYNONYMS = {
    "romantic": "romance",
    "sci-fi": "science fiction",
    "scifi": "science fiction",
    "musical": "music",
    "cartoon": "animation",
    "animated": "animation",
    "doc": "documentary",
    "biopic": "drama",
    "family-friendly": "family",
    "kids": "family",
    "warfare": "war",
    "historical": "history",
    # Add more as needed
}

@app.route('/')
def home():
    return "✅ Smart Movie Recommender backend is running!"

@app.route('/health')
def health():
    return jsonify({"extract_genres": "/extract-genres", "discover_movies": "/discover-movies", "status": "ok"})

# 🎯 Extract genres using Gemini
@app.route('/extract-genres', methods=['POST'])
def extract_genres():
    user_input = request.json.get('query')

    prompt = f"""Extract movie preferences from this sentence:
"{user_input}"

Return a JSON object with:
- genres (list of strings)
- mood (optional)
- duration_limit_minutes (optional integer)
- exclusions (optional list like 'violence', 'horror')"""

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }

    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    response = requests.post(url, headers=headers, data=json.dumps(body))

    print("[DEBUG] Gemini raw response:", response.text)

    try:
        result = response.json()
        # Fallback if Gemini returns an error
        if 'error' in result:
            print("[DEBUG] Gemini error detected, using keyword fallback.")
            user_text = user_input.lower() if user_input else ''
            found_genres = set()
            # Only add direct matches from GENRE_MAPPING
            for genre in GENRE_MAPPING.keys():
                if genre in user_text:
                    found_genres.add(genre.title())
            # Add mapped genres from synonyms/partials
            for word, mapped_genre in GENRE_SYNONYMS.items():
                if word in user_text and mapped_genre in GENRE_MAPPING:
                    found_genres.add(mapped_genre.title())
            found_genres = list(found_genres)
            print("[DEBUG] Fallback genre extraction from user input. Text:", user_text, "Found genres:", found_genres)
            return jsonify({
                "genres": found_genres,
                "note": "Fallback: Gemini unavailable, genres extracted from user input keywords and synonyms.",
                "output": user_input
            })

        parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        if not parts:
            return jsonify({"genres": [], "note": "No candidates returned by Gemini."})

        try:
            # Remove markdown wrappers
            text = parts[0]["text"].strip().strip("```json").strip("```").strip()
            parsed = json.loads(text)
            # Always return a genres key
            if "genres" not in parsed or not isinstance(parsed["genres"], list):
                parsed["genres"] = []
            return jsonify(parsed)
        except json.JSONDecodeError:
            # Try to extract genres from plain text fallback
            text = parts[0]["text"].lower()
            found_genres = []
            for genre in GENRE_MAPPING.keys():
                if genre in text:
                    found_genres.append(genre.title())
            print("[DEBUG] Fallback genre extraction. Text:", text, "Found genres:", found_genres)
            return jsonify({
                "genres": found_genres,
                "note": "Fallback: genres extracted from plain text.",
                "output": parts[0]["text"]
            })

    except Exception as e:
        return jsonify({
            "genres": [],
            "error": "Gemini request failed.",
            "details": str(e),
            "raw": response.text
        }), 500

# 🎬 Discover movies using TMDb
@app.route('/discover-movies', methods=['POST'])
def discover_movies():
    try:
        genre_names = request.json.get('genres', [])
        runtime_limit = request.json.get('duration_limit_minutes')

        print(f"[DEBUG] Incoming genres: {genre_names}")  # Log for debugging

        # Only use mapped genres directly, not fuzzy substring matching
        genre_ids = [GENRE_MAPPING[g.lower()] for g in genre_names if g.lower() in GENRE_MAPPING]

        if not genre_ids:
            return jsonify({"error": "No valid genres provided after fuzzy matching.", "received": genre_names}), 400

        url = (
            f"https://api.themoviedb.org/3/discover/movie"
            f"?api_key={TMDB_API_KEY}"
            f"&language=en-US"
            f"&include_adult=false"
            f"&with_genres={','.join(map(str, genre_ids))}"
            f"&sort_by=popularity.desc"
            f"&vote_average.gte=6"
        )

        if runtime_limit:
            url += f"&with_runtime.lte={runtime_limit}"

        print("[DEBUG] TMDb API URL:", url)
        response = requests.get(url)
        print("[DEBUG] TMDb raw response:", response.text)
        data = response.json()

        if 'errors' in data or 'status_code' in data:
            print("[DEBUG] TMDb error:", data)
            return jsonify({"error": "TMDb API error.", "details": data}), 502

        results = []
        for movie in data.get("results", [])[:10]:
            results.append({
                "title": movie.get("title"),
                "overview": movie.get("overview"),
                "release_date": movie.get("release_date"),
                "poster_path": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None
            })

        if not results:
            print("[DEBUG] No movies found in TMDb response.")
            return jsonify({"error": "No movies found for the given genres.", "genres": genre_names}), 404

        return jsonify(results)

    except Exception as e:
        return jsonify({
            "error": "Error fetching data from TMDb.",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    print("=== Flask app running on http://localhost:5000 ===")
    app.run(debug=True, port=5000)

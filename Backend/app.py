
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
import re
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')

# Database Configuration (SQLite for development)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cinechat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
db.init_app(app)

# ✅ Replace with your actual keys
GEMINI_API_KEY = "AIzaSyBqpiVebxz4nVz3re7MN1avq-kx6qrHBeg"
TMDB_API_KEY = "8e2d9acdba2afa99e751607fbb17535e"

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Renamed 'query' to 'search_text' to avoid conflict with SQLAlchemy's query property
class UserQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    search_text = db.Column(db.String, nullable=False)

# 🎭 Enhanced Genre mapping for TMDb with synonyms
GENRE_MAPPING = {
    # Action & Adventure
    "action": 28, "adventure": 12, "fighting": 28, "battle": 28, "war": 10752,
    "superhero": 28, "martial arts": 28, "explosion": 28, "chase": 28,
    
    # Animation & Family
    "animation": 16, "animated": 16, "cartoon": 16, "family": 10751, "kids": 10751,
    "children": 10751, "child": 10751, "disney": 16, "pixar": 16,
    
    # Comedy & Humor
    "comedy": 35, "funny": 35, "humor": 35, "humorous": 35, "hilarious": 35,
    "laugh": 35, "joke": 35, "satire": 35, "parody": 35,
    
    # Drama & Romance
    "drama": 18, "romance": 10749, "romantic": 10749, "love": 10749, "relationship": 18,
    "emotional": 18, "touching": 18, "heartwarming": 18, "tearjerker": 18,
    
    # Horror & Thriller
    "horror": 27, "scary": 27, "frightening": 27, "terrifying": 27, "thriller": 53,
    "suspense": 53, "mystery": 9648, "suspenseful": 53, "creepy": 27,
    
    # Sci-Fi & Fantasy
    "science fiction": 878, "sci-fi": 878, "fantasy": 14, "magical": 14, "wizard": 14,
    "space": 878, "alien": 878, "robot": 878, "future": 878, "time travel": 878,
    
    # Crime & Mystery
    "crime": 80, "detective": 80, "police": 80, "murder": 80, "investigation": 9648,
    "mystery": 9648, "whodunit": 9648, "suspense": 53,
    
    # Historical & War
    "history": 36, "historical": 36, "period": 36, "medieval": 36, "ancient": 36,
    "war": 10752, "military": 10752, "battle": 10752, "soldier": 10752,
    
    # Music & Documentary
    "music": 10402, "musical": 10402, "concert": 10402, "documentary": 99,
    "real": 99, "true story": 99, "biography": 99,
    
    # Western & Other
    "western": 37, "cowboy": 37, "tv movie": 10770
}

# 🚫 Exclusion mappings - genres to avoid
EXCLUSION_MAPPING = {
    "horror": [27],  # Horror genre ID
    "violence": [28, 80, 10752],  # Action, Crime, War
    "scary": [27, 53],  # Horror, Thriller
    "frightening": [27, 53],
    "terrifying": [27, 53],
    "creepy": [27, 53],
    "gore": [27, 80],  # Horror, Crime
    "blood": [27, 80, 28],  # Horror, Crime, Action
    "murder": [80, 27],  # Crime, Horror
    "death": [80, 27, 10752],  # Crime, Horror, War
    "war": [10752],  # War genre
    "fighting": [28, 10752],  # Action, War
    "battle": [28, 10752],  # Action, War
    "military": [10752],  # War
    "soldier": [10752],  # War
    "crime": [80],  # Crime
    "police": [80],  # Crime
    "detective": [80],  # Crime
}

# 🛡️ Adult content keywords to filter out
ADULT_CONTENT_KEYWORDS = [
    "porn", "sex", "nude", "nudity", "explicit", "adult", "mature",
    "erotic", "sensual", "intimate", "sexual", "romance novel",
    "adult film", "adult movie", "adult content", "x-rated", "r-rated"
]

# Endpoint for signup
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    # Log the user in after signup
    session['user_id'] = new_user.id
    return jsonify({'message': 'User created successfully', 'user': {'id': new_user.id, 'username': new_user.username, 'email': new_user.email}})

# Alias for signup (frontend uses /register)
@app.route('/register', methods=['POST'])
def register():
    return signup()

# Endpoint for login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        return jsonify({
            'message': 'Login successful',
            'user': {'id': user.id, 'username': user.username, 'email': user.email}
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# Endpoint for logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'})

# Endpoint to get user profile
@app.route('/user/profile', methods=['GET'])
def get_user_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email})

# Endpoint to get user search history (real DB version)
@app.route('/user/history', methods=['GET'])
def get_user_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    queries = UserQuery.query.filter_by(user_id=user_id).order_by(UserQuery.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    history = [
        {'id': q.id, 'query': q.search_text} for q in queries.items
    ]
    return jsonify({
        'history': history,
        'current_page': page,
        'pages': queries.pages,
        'total': queries.total
    })

# Endpoint to delete search history item (real DB version)
@app.route('/user/history/<int:search_id>', methods=['DELETE'])
def delete_search_history(search_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    query = UserQuery.query.filter_by(id=search_id, user_id=user_id).first()
    if not query:
        return jsonify({'error': 'Query not found'}), 404
    db.session.delete(query)
    db.session.commit()
    return jsonify({'message': 'Search history deleted successfully'})

# Endpoint to store query for a user (auto user from session)
@app.route('/store-query', methods=['POST'])
def store_query():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    query_text = data.get('query')
    new_query = UserQuery(user_id=user_id, search_text=query_text)
    db.session.add(new_query)
    db.session.commit()
    return jsonify({'message': 'Query stored successfully'})

@app.route('/')
def home():
    return "✅ Smart Movie Recommender backend is running!"

@app.route('/debug-genres', methods=['POST'])
def debug_genres():
    """Debug endpoint to see what's happening with genre extraction"""
    user_input = request.json.get('query', '').lower()
    
    # Test all the extraction functions
    fallback_genres = extract_genres_from_text(user_input)
    fallback_exclusions = extract_exclusions_from_text(user_input)
    final_genres = remove_excluded_genres(fallback_genres, fallback_exclusions)
    
    return jsonify({
        "input": user_input,
        "extracted_genres": fallback_genres,
        "extracted_exclusions": fallback_exclusions,
        "final_genres": final_genres,
        "genre_mapping": {k: v for k, v in GENRE_MAPPING.items() if k in user_input},
        "exclusion_mapping": {k: v for k, v in EXCLUSION_MAPPING.items() if k in user_input}
    })

# 🎯 Enhanced Genre extractor using Gemini
@app.route('/extract-genres', methods=['POST'])
def extract_genres():
    user_input = request.json.get('query', '').lower()
    
    # Enhanced prompt for better genre extraction
    prompt = f"""Analyze this movie request: "{user_input}"

Extract and return a JSON object with:
{{
  "genres": ["list", "of", "genres"],
  "mood": "optional mood description",
  "duration_limit_minutes": optional_integer,
  "exclusions": ["list", "of", "things", "to", "avoid"],
  "additional_filters": {{
    "min_year": optional_year,
    "max_year": optional_year,
    "language": "optional language preference"
  }}
}}

IMPORTANT RULES:
1. If user says "scary", "frightening", "creepy" etc. WITHOUT negative words like "no" or "not", 
   treat these as POSITIVE genre indicators for horror/thriller, NOT exclusions.

2. Only add exclusions when user explicitly says "no horror", "not scary", "avoid violence", etc.

3. Context matters: "something scary to watch" = wants horror movies
   "not scary" = exclude horror movies

Focus on identifying:
- Primary genres (action, comedy, drama, horror, etc.)
- Sub-genres (romantic comedy, action thriller, etc.)
- Mood indicators (feel-good, dark, uplifting, etc.)
- Time constraints (under 2 hours, long movies, etc.)
- Exclusions (no violence, no horror, etc.)
- Era preferences (classic, modern, 90s, etc.)

Return only valid JSON, no additional text."""

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

    try:
        result = response.json()
        print("Gemini API raw response:", result)  # Log Gemini response for debugging
        parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        if not parts:
            # Fallback: try to extract genres using word mapping
            fallback_genres = extract_genres_from_text(user_input)
            fallback_exclusions = extract_exclusions_from_text(user_input)
            final_genres = remove_excluded_genres(fallback_genres, fallback_exclusions)
            return jsonify({
                "genres": final_genres,
                "mood": extract_mood_from_text(user_input),
                "duration_limit_minutes": extract_duration_from_text(user_input),
                "exclusions": fallback_exclusions,
                "note": "Used fallback genre extraction due to Gemini API returning no candidates"
            })

        try:
            # Handle Markdown-wrapped JSON
            text = parts[0]["text"].strip().strip("```json").strip("```").strip()
            parsed = json.loads(text)
            
            # Enhance with word mapping and exclusions
            enhanced_genres = enhance_genres_with_mapping(parsed.get('genres', []), user_input)
            enhanced_exclusions = enhance_exclusions_with_mapping(parsed.get('exclusions', []), user_input)
            
            # Remove excluded genres from the genre list
            final_genres = remove_excluded_genres(enhanced_genres, enhanced_exclusions)
            
            return jsonify({
                "genres": final_genres,
                "mood": parsed.get('mood', ''),
                "duration_limit_minutes": parsed.get('duration_limit_minutes'),
                "exclusions": enhanced_exclusions,
                "additional_filters": parsed.get('additional_filters', {})
            })
            
        except json.JSONDecodeError:
            # Fallback: try to extract genres using word mapping
            fallback_genres = extract_genres_from_text(user_input)
            fallback_exclusions = extract_exclusions_from_text(user_input)
            final_genres = remove_excluded_genres(fallback_genres, fallback_exclusions)
            
            return jsonify({
                "genres": final_genres,
                "mood": extract_mood_from_text(user_input),
                "duration_limit_minutes": extract_duration_from_text(user_input),
                "exclusions": fallback_exclusions,
                "note": "Used fallback genre extraction due to JSON parse error"
            })

    except Exception as e:
        # Fallback: extract genres directly from text
        fallback_genres = extract_genres_from_text(user_input)
        fallback_exclusions = extract_exclusions_from_text(user_input)
        final_genres = remove_excluded_genres(fallback_genres, fallback_exclusions)
        
        return jsonify({
            "genres": final_genres,
            "mood": extract_mood_from_text(user_input),
            "duration_limit_minutes": extract_duration_from_text(user_input),
            "exclusions": fallback_exclusions,
            "note": "Used fallback extraction due to API error"
        })

def enhance_genres_with_mapping(genres, user_input):
    """Enhance genres using word mapping"""
    enhanced = set(genres)
    
    # Add genres based on word mapping
    for word, genre_id in GENRE_MAPPING.items():
        if word in user_input:
            # Convert genre ID back to name for consistency
            genre_name = get_genre_name_from_id(genre_id)
            if genre_name:
                enhanced.add(genre_name)
    
    return list(enhanced)

def enhance_exclusions_with_mapping(exclusions, user_input):
    """Enhance exclusions using exclusion mapping"""
    enhanced = set(exclusions)
    
    # Add exclusions based on word mapping
    for word, genre_ids in EXCLUSION_MAPPING.items():
        if word in user_input:
            enhanced.add(word)
    
    return list(enhanced)

def remove_excluded_genres(genres, exclusions):
    """Remove genres that match exclusions"""
    if not exclusions:
        return genres
    
    excluded_genre_ids = set()
    for exclusion in exclusions:
        if exclusion in EXCLUSION_MAPPING:
            excluded_genre_ids.update(EXCLUSION_MAPPING[exclusion])
    
    # Convert genre names to IDs for comparison
    genre_ids = []
    for genre in genres:
        if genre.lower() in GENRE_MAPPING:
            genre_ids.append(GENRE_MAPPING[genre.lower()])
    
    # Remove excluded genres
    filtered_genre_ids = [gid for gid in genre_ids if gid not in excluded_genre_ids]
    
    # Convert back to names
    filtered_genres = []
    for gid in filtered_genre_ids:
        genre_name = get_genre_name_from_id(gid)
        if genre_name:
            filtered_genres.append(genre_name)
    
    return filtered_genres

def extract_genres_from_text(text):
    """Fallback: extract genres directly from text"""
    genres = []
    
    # First pass: look for positive genre indicators
    for word, genre_id in GENRE_MAPPING.items():
        if word in text:
            genre_name = get_genre_name_from_id(genre_id)
            if genre_name:
                genres.append(genre_name)
    
    # Second pass: if no genres found, look for mood/theme words that suggest genres
    if not genres:
        mood_to_genre = {
            "scary": "horror",
            "frightening": "horror", 
            "terrifying": "horror",
            "creepy": "horror",
            "suspenseful": "thriller",
            "suspense": "thriller",
            "mysterious": "mystery",
            "mystery": "mystery",
            "funny": "comedy",
            "hilarious": "comedy",
            "romantic": "romance",
            "love": "romance",
            "action": "action",
            "adventure": "adventure",
            "exciting": "action",
            "epic": "action",
            "dramatic": "drama",
            "emotional": "drama",
            "thought-provoking": "drama",
            "sci-fi": "science fiction",
            "space": "science fiction",
            "alien": "science fiction",
            "fantasy": "fantasy",
            "magical": "fantasy",
            "historical": "history",
            "period": "history",
            "war": "war",
            "military": "war",
            "crime": "crime",
            "detective": "crime",
            "police": "crime"
        }
        
        for mood_word, genre_name in mood_to_genre.items():
            if mood_word in text:
                genres.append(genre_name)
                break  # Add one genre and stop to avoid too many
    
    return genres[:3]  # Limit to 3 genres

def extract_exclusions_from_text(text):
    """Extract exclusions from text"""
    exclusions = []
    
    # Only add exclusions if they're clearly meant as exclusions
    # Look for negative words like "no", "not", "avoid", "without"
    negative_indicators = ["no ", "not ", "avoid ", "without ", "don't want", "dont want", "hate", "dislike"]
    
    for word in EXCLUSION_MAPPING.keys():
        if word in text:
            # Check if this word is used in a negative context
            is_negative = any(neg in text for neg in negative_indicators)
            
            # If it's clearly negative, add as exclusion
            if is_negative:
                exclusions.append(word)
            # If it's not clearly negative, don't add as exclusion
            # (it might be a positive genre indicator)
    
    return exclusions

def extract_mood_from_text(text):
    """Extract mood from text"""
    mood_keywords = ["feel good", "uplifting", "inspiring", "relaxing", "exciting", 
                    "thought-provoking", "nostalgic", "dark", "lighthearted", 
                    "intense", "sweet", "epic", "cozy", "adrenaline"]
    
    for mood in mood_keywords:
        if mood in text:
            return mood
    return ""

def extract_duration_from_text(text):
    """Extract duration from text"""
    # Look for patterns like "under 2 hours", "90 minutes", etc.
    patterns = [
        r'under (\d+) hours?',
        r'(\d+) hours? or less',
        r'(\d+) minutes? or less',
        r'under (\d+) minutes?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            hours = int(match.group(1))
            if 'hour' in pattern:
                return hours * 60
            else:
                return hours
    
    return None

def get_genre_name_from_id(genre_id):
    """Convert genre ID back to name"""
    reverse_mapping = {v: k for k, v in GENRE_MAPPING.items()}
    return reverse_mapping.get(genre_id)

# 🎬 Enhanced Discover movies from TMDb with family-friendly filtering
@app.route('/discover-movies', methods=['POST'])
def discover_movies():
    try:
        data = request.json
        genre_names = data.get('genres', [])
        runtime_limit = data.get('duration_limit_minutes')
        exclusions = data.get('exclusions', [])
        family_friendly = data.get('family_friendly', True)  # Default to True
        additional_filters = data.get('additional_filters', {})

        # Map genre names to IDs
        genre_ids = []
        for genre in genre_names:
            if genre.lower() in GENRE_MAPPING:
                genre_ids.append(GENRE_MAPPING[genre.lower()])
            else:
                # Try to find partial matches
                for key, value in GENRE_MAPPING.items():
                    if key in genre.lower() or genre.lower() in key:
                        genre_ids.append(value)
                        break

        if not genre_ids:
            return jsonify({"error": "No valid genres provided."}), 400

        # Build TMDb URL with enhanced filters
        base_url = f"https://api.themoviedb.org/3/discover/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "with_genres": ",".join(map(str, genre_ids)),
            "sort_by": "popularity.desc",
            "include_adult": False,  # ✅ Always exclude adult content
            "include_video": False,
            "page": 1
        }

        # Add family-friendly certification filters
        if family_friendly:
            params["certification_country"] = "US"
            params["certification.lte"] = "PG-13"  # Only G, PG, and PG-13 movies

        # Add runtime filter
        if runtime_limit:
            params["with_runtime.lte"] = runtime_limit

        # Add year filters
        if additional_filters.get('min_year'):
            params["primary_release_date.gte"] = f"{additional_filters['min_year']}-01-01"
        if additional_filters.get('max_year'):
            params["primary_release_date.lte"] = f"{additional_filters['max_year']}-12-31"

        response = requests.get(base_url, params=params)
        data = response.json()

        # Filter out excluded content and adult content
        results = []
        for movie in data.get("results", [])[:25]:  # Get more results for filtering
            # Skip movies with excluded content
            if should_exclude_movie(movie, exclusions):
                continue
            
            # Skip adult content
            if is_adult_content(movie):
                continue
                
            results.append({
                "title": movie.get("title"),
                "overview": movie.get("overview"),
                "release_date": movie.get("release_date"),
                "poster_path": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None,
                "vote_average": movie.get("vote_average"),
                "genre_ids": movie.get("genre_ids", [])
            })
            
            if len(results) >= 10:  # Limit to 10 results
                break

        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            "error": "Error fetching data from TMDb.",
            "details": str(e)
        }), 500

# 🎭 Watchlist Explainer - Search movies by title
@app.route('/search-movies', methods=['POST'])
def search_movies():
    try:
        data = request.json
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Search TMDb for movies with better parameters
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "query": query,
            "page": 1,
            "include_adult": False,
            "region": "US",  # Focus on US releases
            "year": None  # Allow any year
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Enhanced result filtering and scoring
        results = []
        query_lower = query.lower()
        
        for movie in data.get("results", [])[:10]:  # Get more results for better filtering
            title = movie.get("title", "").lower()
            original_title = movie.get("original_title", "").lower()
            
            # Calculate relevance score
            score = 0
            
            # Exact title match gets highest score
            if title == query_lower or original_title == query_lower:
                score += 100
            # Starts with query
            elif title.startswith(query_lower) or original_title.startswith(query_lower):
                score += 50
            # Contains query
            elif query_lower in title or query_lower in original_title:
                score += 30
            # Partial word match
            else:
                query_words = query_lower.split()
                title_words = title.split()
                for q_word in query_words:
                    if any(q_word in t_word for t_word in title_words):
                        score += 10
            
            # Boost score for popular movies
            if movie.get("vote_average", 0) > 7.0:
                score += 20
            if movie.get("popularity", 0) > 50:
                score += 15
            
            # Only include movies with reasonable relevance
            if score > 5:
                results.append({
                    "id": movie.get("id"),
                    "title": movie.get("title"),
                    "overview": movie.get("overview"),
                    "release_date": movie.get("release_date"),
                    "poster_path": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None,
                    "vote_average": movie.get("vote_average"),
                    "genre_ids": movie.get("genre_ids", []),
                    "score": score
                })
        
        # Sort by relevance score and return top 5
        results.sort(key=lambda x: x["score"], reverse=True)
        final_results = results[:5]
        
        # Remove score from final results
        for result in final_results:
            result.pop("score", None)
        
        return jsonify(final_results)
        
    except Exception as e:
        return jsonify({
            "error": "Error searching movies",
            "details": str(e)
        }), 500

# 🧠 Watchlist Explainer - Analyze watchlist with Gemini
@app.route('/analyze-watchlist', methods=['POST'])
def analyze_watchlist():
    try:
        data = request.json
        movies = data.get('movies', [])
        
        if not movies or len(movies) == 0:
            return jsonify({"error": "No movies provided"}), 400
        
        # Prepare movie data for analysis
        movie_summaries = []
        for movie in movies:
            summary = f"Title: {movie.get('title', 'Unknown')}"
            if movie.get('overview'):
                summary += f"\nPlot: {movie.get('overview')}"
            if movie.get('release_date'):
                summary += f"\nYear: {movie.get('release_date', '')[:4]}"
            movie_summaries.append(summary)
        
        movies_text = "\n\n".join(movie_summaries)
        
        # Try to get analysis from Gemini API
        try:
            # Create Gemini prompt for personality analysis
            prompt = f"""Analyze these favorite movies and create a personality-style summary:

{movies_text}

Based on these movies, generate a short, engaging personality summary (2-3 sentences) that captures the viewer's taste. Focus on:
- Common themes (complex stories, emotional depth, visual spectacle, etc.)
- Genre preferences
- Storytelling style preferences
- Character types they enjoy
- Overall viewing personality

Format your response as JSON:
{{
  "personality_summary": "Your personality summary here",
  "common_themes": ["theme1", "theme2", "theme3"],
  "preferred_genres": ["genre1", "genre2", "genre3"],
  "viewing_style": "description of their viewing preferences"
}}

Keep the personality summary conversational and engaging, like you're describing a friend's taste in movies."""
            
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
            response = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                
                if parts:
                    try:
                        # Parse Gemini response
                        text = parts[0]["text"].strip().strip("```json").strip("```").strip()
                        analysis = json.loads(text)
                        return jsonify(analysis)
                    except json.JSONDecodeError:
                        pass  # Fall through to fallback analysis
            
        except Exception as api_error:
            pass  # Fall through to fallback analysis
        
        # Fallback analysis - always return something
        movie_titles = [movie.get('title', 'Unknown') for movie in movies]
        titles_text = ", ".join(movie_titles)
        
        # Create a simple but personalized analysis based on the movies
        if len(movies) == 1:
            personality_summary = f"You're drawn to films like '{movie_titles[0]}' - movies that offer unique storytelling and memorable experiences."
        else:
            personality_summary = f"Your taste spans across films like {titles_text}, showing an appreciation for diverse storytelling and quality cinema."
        
        # Extract some basic themes from movie titles and overviews
        themes = []
        genres = []
        
        for movie in movies:
            title = movie.get('title', '').lower()
            overview = movie.get('overview', '').lower()
            
            # Simple theme detection
            if any(word in title or word in overview for word in ['action', 'adventure', 'thriller']):
                themes.append('action and excitement')
                genres.append('action')
            if any(word in title or word in overview for word in ['drama', 'emotional', 'character']):
                themes.append('character-driven stories')
                genres.append('drama')
            if any(word in title or word in overview for word in ['comedy', 'funny', 'humor']):
                themes.append('humor and entertainment')
                genres.append('comedy')
            if any(word in title or word in overview for word in ['sci-fi', 'fantasy', 'superhero']):
                themes.append('imaginative worlds')
                genres.append('sci-fi/fantasy')
            if any(word in title or word in overview for word in ['mystery', 'suspense', 'thriller']):
                themes.append('suspense and intrigue')
                genres.append('thriller')
        
        # Remove duplicates and ensure we have some themes
        themes = list(set(themes))[:3] if themes else ['quality storytelling', 'entertainment']
        genres = list(set(genres))[:3] if genres else ['diverse']
        
        viewing_style = "You appreciate well-crafted films that offer both entertainment and substance."
        
        return jsonify({
            "personality_summary": personality_summary,
            "common_themes": themes,
            "preferred_genres": genres,
            "viewing_style": viewing_style,
            "note": "Generated from your watchlist"
        })
            
    except Exception as e:
        # Ultimate fallback
        return jsonify({
            "personality_summary": "You have excellent taste in movies! Your watchlist shows an appreciation for quality cinema.",
            "common_themes": ["quality filmmaking", "entertainment", "storytelling"],
            "preferred_genres": ["diverse"],
            "viewing_style": "appreciative of good cinema",
            "note": "Fallback analysis"
        })

# 🎬 Watchlist Explainer - Get similar movie recommendations
@app.route('/get-similar-movies', methods=['POST'])
def get_similar_movies():
    try:
        data = request.json
        movie_ids = data.get('movie_ids', [])
        
        if not movie_ids:
            return jsonify({"error": "No movie IDs provided"}), 400
        
        all_recommendations = []
        seen_movies = set()
        watchlist_genres = set()
        
        # First, get genre information from watchlist movies
        for movie_id in movie_ids[:3]:
            # Get detailed movie info including genres
            url = f"https://api.themoviedb.org/3/movie/{movie_id}"
            params = {
                "api_key": TMDB_API_KEY,
                "language": "en-US",
                "append_to_response": "genres"
            }
            
            response = requests.get(url, params=params)
            movie_data = response.json()
            
            # Collect genres from watchlist
            if movie_data.get("genres"):
                for genre in movie_data["genres"]:
                    watchlist_genres.add(genre["id"])
        
        # Get recommendations using multiple methods
        for movie_id in movie_ids[:3]:  # Limit to 3 movies to avoid too many requests
            # Method 1: TMDb recommendations
            url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations"
            params = {
                "api_key": TMDB_API_KEY,
                "language": "en-US",
                "page": 1
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # Add recommendations with genre scoring
            for movie in data.get("results", [])[:8]:  # Get more results for better filtering
                movie_id = movie.get("id")
                if movie_id not in seen_movies:
                    seen_movies.add(movie_id)
                    
                    # Calculate genre similarity score
                    movie_genres = set(movie.get("genre_ids", []))
                    genre_overlap = len(watchlist_genres.intersection(movie_genres))
                    genre_score = genre_overlap * 10  # Boost score for genre matches
                    
                    all_recommendations.append({
                        "id": movie_id,
                        "title": movie.get("title"),
                        "overview": movie.get("overview"),
                        "release_date": movie.get("release_date"),
                        "poster_path": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None,
                        "vote_average": movie.get("vote_average"),
                        "genre_ids": movie.get("genre_ids", []),
                        "genre_score": genre_score
                    })
        
        # Method 2: Discover movies by common genres
        if watchlist_genres:
            genre_list = list(watchlist_genres)[:3]  # Use top 3 genres
            url = "https://api.themoviedb.org/3/discover/movie"
            params = {
                "api_key": TMDB_API_KEY,
                "language": "en-US",
                "with_genres": ",".join(map(str, genre_list)),
                "sort_by": "popularity.desc",
                "include_adult": False,
                "include_video": False,
                "page": 1
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # Add genre-based discoveries
            for movie in data.get("results", [])[:10]:
                movie_id = movie.get("id")
                if movie_id not in seen_movies:
                    seen_movies.add(movie_id)
                    
                    # Calculate genre similarity score
                    movie_genres = set(movie.get("genre_ids", []))
                    genre_overlap = len(watchlist_genres.intersection(movie_genres))
                    genre_score = genre_overlap * 15  # Higher score for genre-based discoveries
                    
                    all_recommendations.append({
                        "id": movie_id,
                        "title": movie.get("title"),
                        "overview": movie.get("overview"),
                        "release_date": movie.get("release_date"),
                        "poster_path": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None,
                        "vote_average": movie.get("vote_average"),
                        "genre_ids": movie.get("genre_ids", []),
                        "genre_score": genre_score
                    })
        
        # Sort by combined score (genre similarity + vote average)
        for rec in all_recommendations:
            rec["combined_score"] = rec["genre_score"] + (rec.get("vote_average", 0) * 2)
        
        all_recommendations.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Remove scoring fields and return top 12 recommendations
        final_results = []
        for rec in all_recommendations[:12]:
            rec.pop("genre_score", None)
            rec.pop("combined_score", None)
            final_results.append(rec)
        
        return jsonify(final_results)
        
    except Exception as e:
        return jsonify({
            "error": "Error getting similar movies",
            "details": str(e)
        }), 500

def is_adult_content(movie):
    """Check if movie contains adult content"""
    title = movie.get("title", "").lower()
    overview = movie.get("overview", "").lower()
    
    # Check if movie is marked as adult
    if movie.get("adult", False):
        return True
    
    # Check for adult content keywords in title or overview
    for keyword in ADULT_CONTENT_KEYWORDS:
        if keyword in title or keyword in overview:
            return True
    
    return False

def should_exclude_movie(movie, exclusions):
    """Check if movie should be excluded based on exclusions list"""
    if not exclusions:
        return False
        
    title = movie.get("title", "").lower()
    overview = movie.get("overview", "").lower()
    genre_ids = movie.get("genre_ids", [])
    
    # Check genre-based exclusions
    for exclusion in exclusions:
        if exclusion in EXCLUSION_MAPPING:
            excluded_genre_ids = EXCLUSION_MAPPING[exclusion]
            # If movie has any of the excluded genres, exclude it
            if any(gid in genre_ids for gid in excluded_genre_ids):
                return True
    
    # Check text-based exclusions
    for exclusion in exclusions:
        if exclusion.lower() in title or exclusion.lower() in overview:
            return True
    
    return False

if __name__ == "__main__":
    print("=== Flask app running on http://localhost:5000 ===")
    app.run(host="0.0.0.0", port=5000, debug=True)
import React, { useState, useEffect } from "react";
import "./App.css";

// Use your Codespaces backend URL here:
const BACKEND_URL = "https://legendary-lamp-9v5w945xwq73w4r-5000.app.github.dev";

function App() {
  // Authentication state
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authMode, setAuthMode] = useState("login"); // "login" or "register"

  // Form states
  const [authForm, setAuthForm] = useState({
    username: "",
    email: "",
    password: ""
  });
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  // App state
  const [activeTab, setActiveTab] = useState("recommendations"); // "recommendations", "watchlist", or "history"

  // Recommendations tab state
  const [query, setQuery] = useState("");
  const [movies, setMovies] = useState([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [loading, setLoading] = useState(false);

  // Watchlist Explainer tab state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [personalityAnalysis, setPersonalityAnalysis] = useState(null);
  const [similarMovies, setSimilarMovies] = useState([]);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);

  // Search History tab state
  const [searchHistory, setSearchHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Check authentication status on app load
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/user/profile`, {
        credentials: 'include'
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  // Authentication functions
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError("");

    try {
      const endpoint = authMode === "login" ? "/login" : "/register";
      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify(authForm)
      });

      const data = await response.json();

      if (response.ok) {
        setUser(data.user);
        setIsAuthenticated(true);
        setAuthError("");
        setAuthForm({ username: "", email: "", password: "" });
      } else {
        setAuthError(data.error || "Authentication failed");
      }
    } catch (error) {
      setAuthError("Network error. Please try again.");
    }

    setAuthLoading(false);
  };

  const handleLogout = async () => {
    try {
      await fetch(`${BACKEND_URL}/logout`, {
        method: "POST",
        credentials: 'include'
      });
    } catch (error) {
      console.error("Logout error:", error);
    }

    setUser(null);
    setIsAuthenticated(false);
    setActiveTab("recommendations");
    setMovies([]);
    setWatchlist([]);
    setSearchHistory([]);
  };

  const loadSearchHistory = async (page = 1) => {
    setHistoryLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/user/history?page=${page}&per_page=5`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setSearchHistory(data.history);
        setCurrentPage(data.current_page);
        setTotalPages(data.pages);
      }
    } catch (error) {
      console.error("Failed to load search history:", error);
    }
    setHistoryLoading(false);
  };

  const deleteSearchHistory = async (searchId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/user/history/${searchId}`, {
        method: "DELETE",
        credentials: 'include'
      });

      if (response.ok) {
        // Reload current page
        loadSearchHistory(currentPage);
      }
    } catch (error) {
      console.error("Failed to delete search:", error);
    }
  };

  // Recommendations tab functions
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    setMovies([]);

    try {
      // Step 1: Extract genres and filters using Gemini
      const extractRes = await fetch(`${BACKEND_URL}/extract-genres`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify({ query }),
      });

      if (!extractRes.ok) {
        throw new Error("Failed to extract genres. Server error.");
      }
      const extractData = await extractRes.json();

      if (!extractData.genres || extractData.genres.length === 0) {
        setErrorMsg("Couldn't extract genres from your input.");
        setLoading(false);
        return;
      }

      // Step 2: Discover movies using TMDb
      const discoverRes = await fetch(`${BACKEND_URL}/discover-movies`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify({
          query: query, // Include original query for history
          genres: extractData.genres || [],
          duration_limit_minutes: extractData.duration_limit_minutes || null,
        }),
      });

      if (!discoverRes.ok) {
        throw new Error("Failed to fetch movie recommendations. Server error.");
      }
      const movieData = await discoverRes.json();

      if (Array.isArray(movieData) && movieData.length > 0) {
        setMovies(movieData);
      } else {
        setErrorMsg("No movies found for your preferences. Try a different query!");
      }
      // Always save the query
      await fetch(`${BACKEND_URL}/store-query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify({ query })
      });
    } catch (error) {
      console.error("Frontend error:", error);
      setErrorMsg(error.message || "Something went wrong. Please try again.");
    }

    setLoading(false);
  };

  // Watchlist Explainer tab functions
  const handleSearchMovies = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearchLoading(true);
    setSearchResults([]);

    try {
      const response = await fetch(`${BACKEND_URL}/search-movies`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify({ query: searchQuery }),
      });

      if (!response.ok) {
        throw new Error("Failed to search movies");
      }

      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error("Search error:", error);
      setErrorMsg("Failed to search movies. Please try again.");
    }

    setSearchLoading(false);
  };

  const addToWatchlist = (movie) => {
    if (!watchlist.find(m => m.id === movie.id)) {
      setWatchlist([...watchlist, movie]);
    }
  };

  const removeFromWatchlist = (movieId) => {
    setWatchlist(watchlist.filter(m => m.id !== movieId));
  };

  const analyzeWatchlist = async () => {
    if (watchlist.length === 0) return;

    setWatchlistLoading(true);
    setPersonalityAnalysis(null);
    setSimilarMovies([]);

    try {
      // Step 1: Analyze personality
      const analysisRes = await fetch(`${BACKEND_URL}/analyze-watchlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify({ movies: watchlist }),
      });

      if (!analysisRes.ok) {
        throw new Error("Failed to analyze watchlist");
      }

      const analysis = await analysisRes.json();
      setPersonalityAnalysis(analysis);

      // Step 2: Get similar movies
      const movieIds = watchlist.map(m => m.id);
      const similarRes = await fetch(`${BACKEND_URL}/get-similar-movies`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify({ movie_ids: movieIds }),
      });

      if (!similarRes.ok) {
        throw new Error("Failed to get similar movies");
      }

      const similar = await similarRes.json();
      setSimilarMovies(similar);

    } catch (error) {
      console.error("Analysis error:", error);
      setErrorMsg("Failed to analyze watchlist. Please try again.");
    }

    setWatchlistLoading(false);
  };

  const clearWatchlist = () => {
    setWatchlist([]);
    setPersonalityAnalysis(null);
    setSimilarMovies([]);
  };

  // Handle tab changes
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === "history" && isAuthenticated) {
      loadSearchHistory();
    }
  };

  // Authentication Form
  if (!isAuthenticated) {
    return (
      <div className="App">
        <div className="auth-container">
          <div className="auth-header">
            <h1>CineChat</h1>
            <p>Swipe Right on Movies!</p>
          </div>

          <div className="auth-form-container">
            <div className="auth-tabs">
              <button
                className={`auth-tab ${authMode === "login" ? "active" : ""}`}
                onClick={() => setAuthMode("login")}
              >
                Login
              </button>
              <button
                className={`auth-tab ${authMode === "register" ? "active" : ""}`}
                onClick={() => setAuthMode("register")}
              >
                Register
              </button>
            </div>

            <form className="auth-form" onSubmit={handleAuthSubmit}>
              <input
                type="text"
                placeholder="Username"
                value={authForm.username}
                onChange={(e) => setAuthForm({ ...authForm, username: e.target.value })}
                required
              />

              {authMode === "register" && (
                <input
                  type="email"
                  placeholder="Email"
                  value={authForm.email}
                  onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                  required
                />
              )}

              <input
                type="password"
                placeholder="Password"
                value={authForm.password}
                onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                required
              />

              {authError && <div className="auth-error">{authError}</div>}

              <button type="submit" disabled={authLoading}>
                {authLoading ? <span className="spinner"></span> : (authMode === "login" ? "Login" : "Register")}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // Main App (Authenticated)
  return (
    <div className="App">
      <div className="app-header">
        <div className="header-content">
          <center><h1>CineChat </h1>
          <p className="subtitle">Find your pick, Swipe Right on Movies!</p>
          </center>
        </div>
        <div className="user-section">
          <span className="welcome-text">Welcome, {user?.username}!</span>
          <button className="logout-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === "recommendations" ? "active" : ""}`}
          onClick={() => handleTabChange("recommendations")}
        >
           Smart Recommendations
        </button>
        <button
          className={`tab-button ${activeTab === "watchlist" ? "active" : ""}`}
          onClick={() => handleTabChange("watchlist")}
        >
          Watchlist Explainer
        </button>
        <button
          className={`tab-button ${activeTab === "history" ? "active" : ""}`}
          onClick={() => handleTabChange("history")}
        >
          My Search History
        </button>
      </div>

      {/* Recommendations Tab */}
      {activeTab === "recommendations" && (
        <div className="tab-content">
          <form className="search-form" onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Tell us what you feel like watching..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              required
            />
            <button type="submit" disabled={loading}>
              {loading ? <span className="spinner"></span> : "Get Movies"}
            </button>
          </form>

          {errorMsg && <div className="error-msg">{errorMsg}</div>}

          <div className="movies">
            {!loading && movies.length === 0 && !errorMsg && (
              <div className="empty-state">
                <p>Start by telling us your mood or favorite genres!</p>
              </div>
            )}
            {movies.map((movie, idx) => (
              <div key={idx} className="movie-card">
                {movie.poster_path && (
                  <img
                    src={movie.poster_path}
                    alt={movie.title}
                  />
                )}
                <div className="movie-info">
                  <h3>{movie.title}</h3>
                  <p className="release-date">{movie.release_date}</p>
                  <p className="overview">{movie.overview}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Watchlist Explainer Tab */}
      {activeTab === "watchlist" && (
        <div className="tab-content">
          <div className="watchlist-section">
            <h2>Add Your Favorite Movies</h2>
            <p>Search and add movies you love to get personalized insights!</p>

            <form className="search-form" onSubmit={handleSearchMovies}>
              <input
                type="text"
                placeholder="Search for a movie (e.g., Inception, The Godfather)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                required
              />
              <button type="submit" disabled={searchLoading}>
                {searchLoading ? <span className="spinner"></span> : "Search"}
              </button>
            </form>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="search-results">
                <h3>Search Results:</h3>
                <div className="movies">
                  {searchResults.map((movie, idx) => (
                    <div key={idx} className="movie-card search-result">
                      {movie.poster_path && (
                        <img
                          src={movie.poster_path}
                          alt={movie.title}
                        />
                      )}
                      <div className="movie-info">
                        <h3>{movie.title}</h3>
                        <p className="release-date">{movie.release_date}</p>
                        <p className="overview">{movie.overview}</p>
                        <button
                          className="add-button"
                          onClick={() => addToWatchlist(movie)}
                          disabled={watchlist.find(m => m.id === movie.id)}
                        >
                          {watchlist.find(m => m.id === movie.id) ? "✓ Added" : "+ Add to Watchlist"}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Current Watchlist */}
            {watchlist.length > 0 && (
              <div className="current-watchlist">
                <div className="watchlist-header">
                  <h3>Your Watchlist ({watchlist.length} movies)</h3>
                  <div className="watchlist-actions">
                    <button
                      className="analyze-button"
                      onClick={analyzeWatchlist}
                      disabled={watchlistLoading}
                    >
                      {watchlistLoading ? <span className="spinner"></span> : " Analyze My Taste"}
                    </button>
                    <button
                      className="clear-button"
                      onClick={clearWatchlist}
                    >
                      Clear All
                    </button>
                  </div>
                </div>

                <div className="watchlist-movies">
                  {watchlist.map((movie, idx) => (
                    <div key={idx} className="watchlist-item">
                      {movie.poster_path && (
                        <img
                          src={movie.poster_path}
                          alt={movie.title}
                          className="watchlist-poster"
                        />
                      )}
                      <div className="watchlist-info">
                        <h4>{movie.title}</h4>
                        <p>{movie.release_date}</p>
                      </div>
                      <button
                        className="remove-button"
                        onClick={() => removeFromWatchlist(movie.id)}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Personality Analysis */}
            {personalityAnalysis && (
              <div className="personality-analysis">
                <h3>🎭 Your Movie Personality</h3>
                <div className="analysis-card">
                  <p className="personality-summary">{personalityAnalysis.personality_summary}</p>
                  <div className="analysis-details">
                    <div className="detail-section">
                      <h4>Common Themes:</h4>
                      <div className="tags">
                        {personalityAnalysis.common_themes?.map((theme, idx) => (
                          <span key={idx} className="tag">{theme}</span>
                        ))}
                      </div>
                    </div>
                    <div className="detail-section">
                      <h4>Preferred Genres:</h4>
                      <div className="tags">
                        {personalityAnalysis.preferred_genres?.map((genre, idx) => (
                          <span key={idx} className="tag">{genre}</span>
                        ))}
                      </div>
                    </div>
                    <div className="detail-section">
                      <h4>Viewing Style:</h4>
                      <p>{personalityAnalysis.viewing_style}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Similar Movies Recommendations */}
            {similarMovies.length > 0 && (
              <div className="similar-movies">
                <h3> Movies You Might Love</h3>
                <p>Based on your watchlist, here are some recommendations:</p>
                <div className="movies">
                  {similarMovies.map((movie, idx) => (
                    <div key={idx} className="movie-card">
                      {movie.poster_path && (
                        <img
                          src={movie.poster_path}
                          alt={movie.title}
                        />
                      )}
                      <div className="movie-info">
                        <h3>{movie.title}</h3>
                        <p className="release-date">{movie.release_date}</p>
                        <p className="overview">{movie.overview}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Search History Tab */}
      {activeTab === "history" && (
        <div className="tab-content">
          <div className="history-section">
            <h2>My Search History</h2>
            <p>View your past movie searches and recommendations</p>

            {historyLoading ? (
              <div className="loading-state">
                <span className="spinner"></span>
                <p>Loading your search history...</p>
              </div>
            ) : searchHistory.length === 0 ? (
              <div className="empty-state">
                <p>No search history yet. Start by making some movie recommendations!</p>
              </div>
            ) : (
              <div className="history-list">
                {searchHistory.map((search) => (
                  <div key={search.id} className="history-item">
                    <div className="history-header">
                      <div className="history-info">
                        <h3>"{search.query}"</h3>
                      </div>
                      <button
                        className="delete-history-button"
                        onClick={() => deleteSearchHistory(search.id)}
                        title="Delete this search"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="pagination">
                    <button
                      className="page-button"
                      onClick={() => loadSearchHistory(currentPage - 1)}
                      disabled={currentPage === 1}
                    >
                      ← Previous
                    </button>
                    <span className="page-info">
                      Page {currentPage} of {totalPages}
                    </span>
                    <button
                      className="page-button"
                      onClick={() => loadSearchHistory(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    >
                      Next →
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

import React, { useState } from "react";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [movies, setMovies] = useState([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    setMovies([]);

    try {
      // Step 1: Extract genres and filters using Gemini
      const extractRes = await fetch("http://localhost:5000/extract-genres", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
      const discoverRes = await fetch("http://localhost:5000/discover-movies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
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
    } catch (error) {
      console.error("Frontend error:", error);
      setErrorMsg(error.message || "Something went wrong. Please try again.");
    }

    setLoading(false);
  };

  return (
    <div className="App">
      <div className="app-header">
        <h1>🎬 CineChat Movie Recommender</h1>
        <p className="subtitle">Get smart, personalized movie picks in seconds!</p>
      </div>
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
              <img src={movie.poster_path} alt={movie.title} />
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
  );
}

export default App;

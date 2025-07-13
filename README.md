#  Smart Movie Recommender

**Natural Language → Personalized Movie Recommendations.**  
Built with Gemini + TMDb APIs. Just say what you feel like watching — we’ll find the perfect movie for you!
---

##  What It Does

Smart Movie Recommender is a web app that lets users type freeform queries like:

> “I feel like watching something emotional and inspiring, under 2 hours.”  
> “Family movie night — no horror or adult content, please!”

The app interprets your intent using **Gemini AI** and fetches **relevant movie suggestions** using **TMDb API**.

---

##  Key Features

✅ Freeform input using natural language  
✅ AI-based genre + mood extraction using **Gemini API**  
✅ Accurate movie suggestions using **TMDb Discover API**  
✅ User login & personalized **search history**  
✅ Bonus: AI-powered **watchlist personality explainer**

---

##  How It Works

### 1.  Intent Understanding with Gemini

- When a user enters a movie request (e.g., “something funny, under 2 hours”)
- The app sends this input to **Google Gemini API** via [Google AI Studio](https://aistudio.google.com/)
- Gemini extracts:
  - 🎞️ Genre (e.g., Comedy, Animation)
  - ⏱️ Runtime (e.g., under 120 minutes)
  - 🚫 Exclusions (e.g., no horror)
  - 😊 Mood (e.g., light-hearted, family-friendly)

### 2.  Movie Fetching with TMDb API

- Genres from Gemini are mapped to TMDb’s official genre IDs via:
  - `https://api.themoviedb.org/3/genre/movie/list`
- A custom query is sent to TMDb’s Discover API:
  - `https://api.themoviedb.org/3/discover/movie`
- Results are filtered based on:
  - Genre
  - Runtime
  - Vote rating
  - Year (if specified)
  - Content safety flags

---

## 🛠️ Tech Stack

| Component  | Tech Used                         |
|------------|-----------------------------------|
| Frontend   | React                             |
| Backend    | Flask (Python)                    |
| AI Engine  | Gemini API (Google AI Studio)     |
| Movie Data | TMDb API                          |
| Database   | PostgreSQL                        |
| Auth       | Secure login with hashed passwords|

---

##  Example Queries

- “In the mood for an inspiring sports movie from the 90s”
- “Animated film under 90 minutes — no violence”
- “Feel-good drama for a rainy evening”

 Gemini converts this into structured filters →  TMDb returns perfect matches.

---

##  Features Implemented

- [x] Natural language query input
- [x] Genre/mood/runtime extraction using Gemini
- [x] Genre mapping and movie fetching using TMDb
- [x] Movie display with posters, descriptions, release year
- [x] User authentication (signup/login)
- [x] Search history page
- [x] Watchlist personality summary (Bonus)

---

##  Improvements & Ideas

- Add speech-to-text input  
- UI polish & mobile responsiveness  
- Gemini Pro for deeper query understanding  
- Multi-language support

---
<img width="1916" height="911" alt="image" src="https://github.com/user-attachments/assets/96decd9e-d002-45a3-ae7a-93724081d084" />
<img width="1913" height="909" alt="image" src="https://github.com/user-attachments/assets/df2ab733-5bfb-4216-a413-c883e2ce1873" />
<img width="1918" height="971" alt="image" src="https://github.com/user-attachments/assets/7f5718f9-b841-4c03-9f53-2f89bfebbf37" />
<img width="1909" height="908" alt="image" src="https://github.com/user-attachments/assets/64acd268-fbac-4d7a-a1dd-914f30541a93" />

##  Setup Instructions

```bash
# Clone the repo
git clone https://github.com/yourusername/smart-movie-recommender.git
cd smart-movie-recommender

# Setup backend
cd Backend
pip install -r requirements.txt
python app.py

# Setup frontend
cd ../Frontend
npm install
npm start











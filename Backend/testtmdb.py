import requests

TMDB_API_KEY = "8e2d9acdba2afa99e751607fbb17535e"
url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US"

try:
    response = requests.get(url)
    print("Status:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("❌ Error:", str(e))

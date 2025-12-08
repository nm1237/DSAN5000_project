import requests
import pandas as pd
import time
from datetime import datetime
import os

# ==========================================
# TMDB DATA COLLECTION SCRIPT
# ==========================================

API_KEY = "b46efa6b7d2a102458d93cc7b0bc7599"  

BASE_URL = "https://api.themoviedb.org/3"

# output directory
OUTPUT_DIR = "../../data/raw-data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_popular_movies(page=1):
    """Get popular movies from TMDB"""
    url = f"{BASE_URL}/discover/movie"
    params = {
        'api_key': API_KEY,
        'language': 'en-US',
        'sort_by': 'popularity.desc',
        'include_adult': 'false',
        'include_video': 'false',
        'page': page,
        'vote_count.gte': 100  # only movies with at least 100 votes
    }
    response = requests.get(url, params=params)
    return response.json()

def get_movie_details(movie_id):
    """Get detailed information for a specific movie"""
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {
        'api_key': API_KEY,
        'append_to_response': 'credits'  # include cast and crew
    }
    response = requests.get(url, params=params)
    return response.json()

def extract_movie_data(movie_details):
    """Extract relevant features from movie details"""
    
    # basic info
    movie_data = {
        'movie_id': movie_details.get('id'),
        'title': movie_details.get('title'),
        'release_date': movie_details.get('release_date'),
        'budget': movie_details.get('budget'),
        'revenue': movie_details.get('revenue'),
        'runtime': movie_details.get('runtime'),
        'vote_average': movie_details.get('vote_average'),
        'vote_count': movie_details.get('vote_count'),
        'popularity': movie_details.get('popularity'),
        'overview': movie_details.get('overview', '')[:500],  # first 500 chars
    }
    
    # extract genres
    genres = movie_details.get('genres', [])
    movie_data['genres'] = '|'.join([g['name'] for g in genres])
    movie_data['primary_genre'] = genres[0]['name'] if genres else None
    
    # extract production companies
    companies = movie_details.get('production_companies', [])
    movie_data['production_companies'] = '|'.join([c['name'] for c in companies[:3]])  # top 3
    
    # extract cast (top 5 actors)
    credits = movie_details.get('credits', {})
    cast = credits.get('cast', [])[:5]
    movie_data['cast'] = '|'.join([actor['name'] for actor in cast])
    movie_data['cast_popularity'] = sum([actor.get('popularity', 0) for actor in cast]) / len(cast) if cast else 0
    
    # extract director
    crew = credits.get('crew', [])
    directors = [person['name'] for person in crew if person['job'] == 'Director']
    movie_data['director'] = directors[0] if directors else None
    
    # extract release month and year
    if movie_data['release_date']:
        try:
            release_dt = datetime.strptime(movie_data['release_date'], '%Y-%m-%d')
            movie_data['release_year'] = release_dt.year
            movie_data['release_month'] = release_dt.month
        except:
            movie_data['release_year'] = None
            movie_data['release_month'] = None
    else:
        movie_data['release_year'] = None
        movie_data['release_month'] = None
    
    return movie_data

def collect_movies(num_pages=250):
    """
    Collect movies from TMDB
    Each page has ~20 movies, so 250 pages = ~5,000 movies
    """
    
    all_movies = []
    movies_collected = 0
    errors = 0
    
    print(f"Starting data collection...")
    print(f"Target: {num_pages} pages (~{num_pages * 20} movies)")
    print("=" * 60)
    
    start_time = time.time()
    
    for page in range(1, num_pages + 1):
        try:
            # get list of movies on this page
            popular_movies = get_popular_movies(page)
            movie_list = popular_movies.get('results', [])
            
            # get detailed info for each movie
            for movie in movie_list:
                try:
                    movie_id = movie['id']
                    details = get_movie_details(movie_id)
                    
                    # only keep movies with budget and revenue data
                    if details.get('budget', 0) > 0 and details.get('revenue', 0) > 0:
                        movie_data = extract_movie_data(details)
                        all_movies.append(movie_data)
                        movies_collected += 1
                    
                    time.sleep(0.25) 
                    
                except Exception as e:
                    errors += 1
                    print(f"Error processing movie ID {movie_id}: {str(e)}")
                    continue
            
            # progress update every 10 pages
            if page % 10 == 0:
                elapsed = time.time() - start_time
                rate = movies_collected / elapsed * 60  # movies per minute
                print(f"Page {page}/{num_pages} | Movies collected: {movies_collected} | "
                      f"Rate: {rate:.1f} movies/min | Errors: {errors}")
        
        except Exception as e:
            print(f"Error on page {page}: {str(e)}")
            errors += 1
            continue
    
    # final summary
    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"Collection complete!")
    print(f"Total movies collected: {movies_collected}")
    print(f"Total errors: {errors}")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    
    return all_movies

def main():
    """Main execution function"""
    
    # check API key
    if API_KEY == "YOUR_API_KEY_HERE":
        print("ERROR: Please replace 'YOUR_API_KEY_HERE' with your actual TMDB API key")
        return
    
    print("🎬 TMDB Movie Data Collection")
    print("=" * 60)
    
    # collect movies
    movies = collect_movies(num_pages=250)
    
    # convert to DataFrame
    df = pd.DataFrame(movies)
    
    # cave to CSV
    output_file = os.path.join(OUTPUT_DIR, 'tmdb_movies_raw.csv')
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Data saved to: {output_file}")
    print(f"📊 Dataset shape: {df.shape[0]} movies × {df.shape[1]} features")
    print("\nColumn names:")
    print(df.columns.tolist())
    
    # quick data preview
    print("\n📋 Sample of collected data:")
    print(df[['title', 'budget', 'revenue', 'primary_genre', 'release_year']].head(10))

if __name__ == "__main__":
    main()
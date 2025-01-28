# IMDb Movie Scraper

This project scrapes movie information from IMDb based on a specified genre and provides APIs to interact with the stored data.

## Features
- Supports scraping of user specified pages based on: genre, title_type, user_rating, num_votes, release_year and pages
- Capable of scraping data from multiple pages
- Input data validation
- Uses asynchronous programming
- Error handling and logging

## Dependencies

- Django
- Django REST Framework
- BeautifulSoup
- playwright
- pytest

## Setup Instructions

1. Clone this repository:\
`git clone https://github.com/yogeshBsht/IMDbScraper.git`\
`cd IMDbScraper/`

2. Install python.\
Check the installed python version: `python --version`
3. Create virtual environment and activate it.
`python -m venv venv`\
`source venv/bin/activate`

2. Install dependencies:\
`pip install -r requirements.txt`

3. Set up the database:\
`python manage.py migrate`

4. Run the scraper:
- Scraping the first page of a genre:\
`python manage.py scrape_movies --genre=comedy`

- Scraping user specified page:\
`python manage.py scrape_movies --genre=comedy --title_type=feature --user_rating=8 --num_votes=100000 --release_year=2020 --pages=2`

5. Start the server:\
`python manage.py runserver`

6. Access the movie APIs at `http://127.0.0.1:8000`.

## Movie API endpoints
#### 1. `GET /movies/<title>/`

This endpoint retrieves the details of a movie based on the provided title.

**Request:**
- **URL**: `/movies/<title>/` (Replace `<title>` with the actual movie title)
- **Method**: `GET`

**curl:**
```bash
curl --location --request GET 'http://localhost:8000/movies/Distant/'
```
  
**Response (Success):**
- **Status Code**: `200 OK`
- **Body**:
```json
{
    "id": 16,
    "title": "Distant",
    "release_year": "2024",
    "duration": "1h 27m",
    "category": "PG-13",
    "imdb_rating": 5.7,
    "director": null,
    "cast": "Naomi Scott and Anthony Ramos",
    "plot_summary": "It follows an asteroid miner who, after crash-landing on an alien planet, must make his way across the harsh terrain, running out of oxygen, hunted by strange creatures, to the only other survivor."
}
```
**Response (Failure):**
- **Status Code**: `404 Not Found`
- **Body**:
```json
{
    "error": "Movie not found"
}
```
#### 2. `POST /movies/<title>/`

This endpoint creates a new movie entry with the provided details.

**Request:**
- **URL**: `/movies/<title>/` (Replace `<title>` with the actual movie title)
- **Method**: `POST`
- **Request Body**:
```json
{
    "title": "Pulp Fiction",
    "release_year": "1994",
    "duration": "154 min",
    "category": "A",
    "imdb_rating": 9.0,
    "director": "Quentin Tarantino",
    "cast": "John Travolta, Uma Thurman, Samuel L. Jackson",
    "plot_summary": "The lives of two mob hitmen, a boxer, a gangster, and his wife intertwine in four tales of violence and redemption."
}
```

**curl:**
```bash
curl --location --request POST 'http://localhost:8000/movies/pulp fiction/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "title": "Pulp Fiction",
    "release_year": "1994",
    "duration": "154 min",
    "category": "A",
    "imdb_rating": 9.0,
    "director": "Quentin Tarantino",
    "cast": "John Travolta, Uma Thurman, Samuel L. Jackson",
    "plot_summary": "The lives of two mob hitmen, a boxer, a gangster, and his wife intertwine in four tales of violence and redemption."
}'
```
  
**Response (Success):**
- **Status Code**: `201 Created`
- **Body**:
```json
{
    "id": 203,
    "title": "Pulp Fiction",
    "release_year": "1994",
    "duration": "154 min",
    "category": "A",
    "imdb_rating": 9.0,
    "director": "Quentin Tarantino",
    "cast": "John Travolta, Uma Thurman, Samuel L. Jackson",
    "plot_summary": "The lives of two mob hitmen, a boxer, a gangster, and his wife intertwine in four tales of violence and redemption."
}
```
**Response (Failure):**
- **Status Code**: `400 Bad Request`
- **Body**:
```json
{
    "title": [
        "movie with this title already exists."
    ]
}
```
#### 3. `PUT /movies/<title>/`

This endpoint updates an existing movie's details. You only need to send the fields you want to update.

**Request:**
- **URL**: `/movies/<title>/` (Replace `<title>` with the actual movie title)
- **Method**: `PUT`
- **Request Body**:
```json
{
    "imdb_rating": 8.9  
}
```

**curl:**
```bash
curl --location --request PUT 'http://localhost:8000/movies/pulp fiction/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "imdb_rating": 8.9  
}'
```
  
**Response (Success):**
- **Status Code**: `200 OK`
- **Body**:
```json
{
    "id": 203,
    "title": "Pulp Fiction",
    "release_year": "1994",
    "duration": "154 min",
    "category": "A",
    "imdb_rating": 8.9,
    "director": "Quentin Tarantino",
    "cast": "John Travolta, Uma Thurman, Samuel L. Jackson",
    "plot_summary": "The lives of two mob hitmen, a boxer, a gangster, and his wife intertwine in four tales of violence and redemption."
}
```
**Response (Failure):**
- **Status Code**: `404 Not Found`
- **Body**:
```json
{
    "error": "Movie not found"
}
```
#### 4. `DELETE /movies/<title>/`

This endpoint creates a new movie entry with the provided details.

**Request:**
- **URL**: `/movies/<title>/` (Replace `<title>` with the actual movie title)
- **Method**: `DELETE`
- **Request Body**:
```json
{
    "title": "pulp fiction"
}
```

**curl:**
```bash
curl --location --request DELETE 'http://localhost:8000/movies/pulp Fiction/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "title": "pulp fiction"
}'
```
  
**Response (Success):**
- **Status Code**: `204 No Content`
- **Body**:
```json
{
    "message": "Movie deleted successfully"
}
```
**Response (Failure):**
- **Status Code**: `404 Not Found`
- **Body**:
```json
{
    "error": "Movie not found"
}
```
#### 5. `GET /movies/`

This endpoint retrieves a list of all movies in the database.

**Request:**
- **URL**: `/movies/`
- **Method**: `GET`

**curl:**
```bash
curl --location --request GET 'http://localhost:8000/movies/'
```
  
**Response (Success):**
- **Status Code**: `200 OK`
- **Body**:
```json
[
    {
        "id": 1,
        "title": "How to Train Your Dragon",
        "release_year": "2025",
        "duration": null,
        "category": null,
        "imdb_rating": null,
        "director": null,
        "cast": "Mason Thames",
        "plot_summary": "Follows a young Viking as he aspires to hunt dragons, and how he unexpectedly becomes a friend of a young dragon."
    },
    {
        "id": 2,
        "title": "Back in Action",
        "release_year": "2025",
        "duration": "1h 54m",
        "category": "PG-13",
        "imdb_rating": 5.9,
        "director": null,
        "cast": "Cameron Diaz and Jamie Foxx",
        "plot_summary": "Former CIA spies Emily and Matt are pulled back into espionage after their secret identities are exposed."
    },
    ...
]
```
## Unit Testing
1. Enable venv: `source venv/bin/activate`
2. Export django settings: `export DJANGO_SETTINGS_MODULE=imdb_scraper.settings`
3. Run the tests: `pytest`

## Disclaimer

This project scrapes data from IMDb, which may violate its terms of service. The author does not claim any affiliation with IMDb and is not responsible for any misuse of the project. Use this project responsibly and only for personal or educational purposes. Ensure compliance with applicable laws and the website's terms before using.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

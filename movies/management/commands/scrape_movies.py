import asyncio
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from django.db import transaction
from django.core.management.base import BaseCommand
from typing import List, Dict, Optional
from playwright.async_api import async_playwright

from movies.models import Movie, Genre, TitleType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Scrape IMDb movies by genre and store in the database"
    BASE_URL = "https://www.imdb.com/search/title/"
    HEADERS = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def add_arguments(self, parser):
        """
        Adds command-line arguments for the scraper script.

        Args:
            parser: An ArgumentParser object to which arguments are added.

        Arguments:
            --genre (str): Genre of the movies (required).
            --title_type (str): Type of the title, with choices from TitleType enum (default: feature).
            --user_rating (float): User rating between 1.0 and 10.0.
            --num_votes (int): Minimum number of votes.
            --release_year (int): Release year (e.g., 2020).
            --pages (int): Number of pages to scrape (default: 1).
        """
        parser.add_argument("--genre", type=str,
                            required=True, help="Genre of the movies")
        parser.add_argument("--title_type", type=str, choices=[
                            t.value for t in TitleType], default=TitleType.FEATURE.value, help="Type of the title (default: feature)")
        parser.add_argument("--user_rating", type=float,
                            help="User rating (1.0 to 10.0)")
        parser.add_argument("--num_votes", type=int,
                            help="Minimum number of votes")
        parser.add_argument("--release_year", type=int,
                            help="Release year (e.g., 2020)")
        parser.add_argument("--pages", type=int, default=1,
                            help="Number of pages to scrape (default is 1)")

    def validate_arguments(self, genre: str, user_rating: float, release_year: int) -> None:
        """
        Validates the command-line arguments to ensure they meet specified constraints.

        Args:
            genre (str): Genre of the movies.
            user_rating (float): User rating between 1.0 and 10.0.
            release_year (int): Release year of the movies.

        Raises:
            ValueError: If the genre is not valid, user_rating is out of range, or release_year 
                        is not within the acceptable range (1900 to the current year).
        """
        if genre not in [g.value for g in Genre]:
            raise ValueError(
                f"Invalid genre: {genre}. Valid options are {[g.value for g in Genre]}.")

        if user_rating is not None and not (1.0 <= user_rating <= 10.0):
            raise ValueError(
                "User rating must be a float between 1.0 and 10.0.")

        if release_year is not None:
            current_year = datetime.now().year
            if release_year < 1900 or release_year > current_year:
                raise ValueError(
                    f"Release year must be between 1900 and {current_year}.")

    def construct_url(self, genre: str, title_type: str, user_rating: float, num_votes: int, release_year: int) -> str:
        """
        Constructs the URL for scraping movies based on the provided parameters.

        Args:
            genre (str): Genre of the movies.
            title_type (str): Type of the title (e.g., feature, documentary).
            user_rating (float): Minimum user rating (optional).
            num_votes (int): Minimum number of votes (optional).
            release_year (int): Release year of the movies (optional).

        Returns:
            str: The constructed URL for scraping.
        """
        url = f"{self.BASE_URL}?title_type={title_type}&genres={genre}"
        current_date = datetime.now().strftime("%Y-%m-%d")

        if user_rating:
            url += f"&user_rating={user_rating},10"
        if num_votes:
            url += f"&num_votes={num_votes},"
        if release_year:
            url += f"&release_date={release_year}-01-01,{current_date}"

        return url

    async def fetch_all_pages_with_playwright(self, url: str, page_count: int) -> Optional[str]:
        """
        Fetches content from all pages using Playwright, simulating user interaction where needed.

        Args:
            url (str): The URL of the first page to fetch.
            page_count (int): The number of pages to fetch.

        Returns:
            Optional[str]: Combined content of all fetched pages, or None if an error occurs.

        Logs:
            - Info when clicking the "50 more" button to load additional content.
            - Info when no "50 more" button is found.
            - Error if an exception occurs during fetching.
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()

                await context.set_extra_http_headers(self.HEADERS)

                page = await context.new_page()
                await page.goto(url)

                all_page_content = ""
                for page_num in range(page_count):
                    # Wait for the page to load and fetch the content
                    await page.wait_for_load_state("networkidle")
                    content = await page.content()
                    all_page_content += content

                    # Locate the "50 more" button using its class
                    button = page.locator("button.ipc-see-more__button")
                    if await button.count() > 0 and await button.is_visible():
                        await button.click()  # Click the button to load more titles
                        logger.info(
                            f"'50 more' button clicked on page {page_num + 1}")
                        # Wait for the next set of content to load
                        await page.wait_for_timeout(2000)
                    else:
                        logger.info(
                            f"No '50 more' button found on page {page_num + 1}")
                        break

                await browser.close()
                return all_page_content
        except Exception as e:
            logger.error(f"Error fetching all pages with Playwright: {e}")
            return None

    async def scrape_page(self, url: str, pages: int) -> List[Dict]:
        """
        Scrapes the given page URL and returns a list of dictionaries containing the scraped data.

        Args:
            url (str): The URL of the page to scrape.
            pages (int): The number of pages to scrape.

        Returns:
            List[Dict]: A list of dictionaries containing scraped data. Returns an empty list if no data is found.
        """
        page_content = await self.fetch_all_pages_with_playwright(url, pages)
        if not page_content:
            logger.info("Cannot scrape as page_content is None")
            return []

        soup = BeautifulSoup(page_content, "html.parser")
        # with open("output.html", "w", encoding="utf-8") as file:
        #     file.write(soup.prettify())

        # Find all movie containers
        movie_containers = soup.find_all(
            "li", class_="ipc-metadata-list-summary-item")
        movies = []

        for container in movie_containers:
            try:
                # Extract title
                title_tag = container.find("h3", class_="ipc-title__text")
                title = title_tag.text.strip() if title_tag else None
                title = title.split(". ")[1] if title else None

                img_tag = container.find("img", class_="ipc-image")
                if img_tag and "alt" in img_tag.attrs:
                    alt_text = img_tag["alt"]
                    cast = alt_text.split(" in ")[0]

                # Extract year, duration, and category
                metadata_div = container.find(
                    "div", class_="sc-300a8231-6 dBUjvq dli-title-metadata")
                year, duration, category = None, None, None
                if metadata_div:
                    metadata_items = metadata_div.find_all(
                        "span", class_="sc-300a8231-7 eaXxft dli-title-metadata-item")
                    if len(metadata_items) >= 1:
                        year = metadata_items[0].text.strip()
                    if len(metadata_items) >= 2:
                        duration = metadata_items[1].text.strip()
                    if len(metadata_items) >= 3:
                        category = metadata_items[2].text.strip()

                # Extract rating
                rating_tag = container.find(
                    "span", class_="ipc-rating-star--rating")
                rating = rating_tag.text.strip() if rating_tag else None

                # vote_count_tag = container.find(
                #     "span", class_="ipc-rating-star--voteCount")
                # vote_count = vote_count_tag.text.strip(
                #     "()").strip() if vote_count_tag else None
                # vote_count = vote_count.replace(
                #     "(", "").replace(")", "") if vote_count else None

                # Extract plot
                plot_tag = container.find(
                    "div", class_="ipc-html-content-inner-div")
                plot = plot_tag.text.strip() if plot_tag else None

                # Create movie dictionary
                movie = {
                    "title": title,
                    "year": year,
                    "duration": duration,
                    "category": category,
                    "rating": rating,
                    "cast": cast,
                    "plot": plot,
                }
                movies.append(movie)
            except Exception as e:
                logger.error(f"Error processing container: {e}")

        # # Print the extracted movies
        # for movie in movies:
        #     print(movie)
        logger.info(f"Scraped movie count is {len(movies)}")
        return movies

    async def scrape_url(self, url: str, max_pages: int) -> List[Dict]:
        """
        Scrapes multiple pages from the given URL and aggregates the results.

        Args:
            url (str): The base URL to scrape.
            max_pages (int): The maximum number of pages to scrape.

        Returns:
            List[Dict]: A list of dictionaries containing movie data from all the scraped pages.
        """
        results = await asyncio.gather(self.scrape_page(url, max_pages))
        movies = [movie for page_movies in results for movie in page_movies]
        return movies

    def save_movies(self, movies: List[Dict]) -> None:
        """
        Saves or updates movie records in the database based on the provided list of movies.

        Args:
            movies (List[Dict]): A list of dictionaries containing movie data to be saved or updated.
                                Each dictionary should include keys like "title", "year", "rating", 
                                "cast", "plot", "duration", and "category".

        Returns:
            None

        Logs:
            - Info if there are no movies to add or update.
            - Info with counts of created and updated records after successful execution.
            - Error if an exception occurs while saving or updating movies.
        """
        try:
            if not movies:
                logger.info("No movie to add or update")
                return

            titles = [movie["title"] for movie in movies]

            # Retrieve existing movies
            existing_movies = Movie.objects.filter(title__in=titles)
            existing_movies_dict = {
                movie.title: movie for movie in existing_movies}

            new_movies = []
            updates = []

            for movie in movies:
                if movie["title"] in existing_movies_dict:
                    # Update the existing movie's attributes
                    existing_movie = existing_movies_dict[movie["title"]]
                    existing_movie.release_year = movie["year"]
                    existing_movie.imdb_rating = movie["rating"]
                    existing_movie.cast = movie["cast"]
                    existing_movie.plot_summary = movie["plot"]
                    existing_movie.duration = movie["duration"]
                    existing_movie.category = movie["category"]
                    updates.append(existing_movie)
                else:
                    # Add new movies
                    new_movies.append(
                        Movie(
                            title=movie["title"],
                            release_year=movie["year"],
                            imdb_rating=movie["rating"],
                            cast=movie["cast"],
                            plot_summary=movie["plot"],
                            duration=movie["duration"],
                            category=movie["category"],
                        )
                    )

            with transaction.atomic():
                # Bulk create new movies
                Movie.objects.bulk_create(new_movies, ignore_conflicts=True)

                # Bulk update existing movies
                if updates:
                    Movie.objects.bulk_update(
                        updates,
                        fields=["release_year", "imdb_rating", "cast",
                                "plot_summary", "duration", "category"]
                    )
            logger.info(
                f"Created {len(new_movies)} & updated {len(updates)} movie records")
        except Exception as e:
            logger.error(f"Error saving movies: {e}")

    def handle(self, *args, **options):
        genre = options["genre"]
        title_type = options["title_type"]
        user_rating = options.get("user_rating")
        num_votes = options.get("num_votes")
        release_year = options.get("release_year")
        pages_to_scrape = options.get("pages")

        try:
            self.validate_arguments(genre, user_rating, release_year)
            url = self.construct_url(
                genre, title_type, user_rating, num_votes, release_year)
            logger.info(f"Scraping IMDb with URL: {url}")
            movies = asyncio.run(self.scrape_url(url, pages_to_scrape))
            self.save_movies(movies)
        except ValueError as e:
            logger.error(e)

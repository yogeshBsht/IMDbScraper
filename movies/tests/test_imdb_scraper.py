import logging
import pytest
from datetime import datetime
from movies.management.commands.scrape_movies import Command
from movies.models import Movie, TitleType
from unittest.mock import Mock, call, patch, MagicMock, AsyncMock

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Mock data for testing
MOCK_HTML = """
<html>
    <body>
        <ul class="ipc-metadata-list-summary">
            <li class="ipc-metadata-list-summary-item">
                <h3 class="ipc-title__text">1. Movie Title 1</h3>
                <img class="ipc-image" alt="Actor A, Actor B in Movie Title 1" />
                <div class="sc-300a8231-6 dBUjvq dli-title-metadata">
                    <span class="sc-300a8231-7 eaXxft dli-title-metadata-item">2023</span>
                    <span class="sc-300a8231-7 eaXxft dli-title-metadata-item">120 min</span>
                    <span class="sc-300a8231-7 eaXxft dli-title-metadata-item">Drama</span>
                </div>
                <span class="ipc-rating-star--rating">8.5</span>
                <span class="ipc-rating-star--voteCount">(1,234)</span>
                <div class="ipc-html-content-inner-div">A summary of the movie.</div>
            </li>
        </ul>
    </body>
</html>
"""


@pytest.fixture
def command():
    """Fixture for the Command instance."""
    return Command()


def test_add_arguments(command):
    parser = Mock()
    command.add_arguments(parser)

    # Check if parser.add_argument was called with expected arguments
    expected_calls = [
        call("--genre", type=str, required=True, help="Genre of the movies"),
        call("--title_type", type=str, choices=[t.value for t in TitleType],
             default=TitleType.FEATURE.value, help="Type of the title (default: feature)"),
        call("--user_rating", type=float, help="User rating (1.0 to 10.0)"),
        call("--num_votes", type=int, help="Minimum number of votes"),
        call("--release_year", type=int, help="Release year (e.g., 2020)"),
        call("--pages", type=int, default=1,
             help="Number of pages to scrape (default is 1)")
    ]
    parser.add_argument.assert_has_calls(expected_calls, any_order=True)


def test_validate_arguments_valid(command):
    # Test valid inputs
    command.validate_arguments(
        genre="comedy", user_rating=8.5, release_year=2020)


def test_validate_arguments_invalid_genre(command):
    with pytest.raises(ValueError, match="Invalid genre: sci-fi"):
        command.validate_arguments(
            genre="sci-fi", user_rating=8.5, release_year=2020)


def test_validate_arguments_invalid_user_rating(command):
    with pytest.raises(ValueError, match="User rating must be a float between 1.0 and 10.0."):
        command.validate_arguments(
            genre="comedy", user_rating=11, release_year=2020)


def test_validate_arguments_invalid_release_year(command):
    with pytest.raises(ValueError, match="Release year must be between 1900 and"):
        command.validate_arguments(
            genre="comedy", user_rating=8.5, release_year=1800)


def test_construct_url_all_arguments(command):
    url = command.construct_url(
        genre="comedy",
        title_type="feature",
        user_rating=8.5,
        num_votes=100000,
        release_year=2020
    )
    current_date = datetime.now().strftime("%Y-%m-%d")
    expected_url = (
        "https://www.imdb.com/search/title/"
        f"?title_type=feature&genres=comedy&user_rating=8.5,10&num_votes=100000,&release_date=2020-01-01,{current_date}"
    )
    assert url == expected_url


def test_construct_url_missing_optional_arguments(command):
    url = command.construct_url(
        genre="action",
        title_type="tv_series",
        user_rating=None,
        num_votes=None,
        release_year=None
    )
    expected_url = "https://www.imdb.com/search/title/?title_type=tv_series&genres=action"
    assert url == expected_url


def test_construct_url_partial_arguments(command):
    url = command.construct_url(
        genre="drama",
        title_type="feature",
        user_rating=7.5,
        num_votes=50000,
        release_year=None
    )
    expected_url = (
        "https://www.imdb.com/search/title/"
        "?title_type=feature&genres=drama&user_rating=7.5,10&num_votes=50000,"
    )
    assert url == expected_url


# @pytest.mark.asyncio
# @patch("movies.management.commands.scrape_movies.async_playwright")
# async def test_fetch_all_pages_with_playwright(mock_playwright):
#     from movies.management.commands.scrape_movies import Command

#     # Mock Playwright browser, context, and page
#     mock_browser = AsyncMock()
#     mock_context = AsyncMock()
#     mock_page = AsyncMock()

#     # Log calls to the mocked methods
#     def log_and_return(value):
#         logger.debug(f"Mocked method called, returning: {value}")
#         return value

#     # Set up the mocked Playwright methods
#     mock_playwright.return_value.chromium.launch.return_value = mock_browser
#     mock_browser.new_context.return_value = mock_context
#     mock_context.new_page.return_value = mock_page

#     # Mock the page behavior
#     mock_page.content.return_value = MOCK_HTML
#     mock_page.locator.return_value = AsyncMock(
#         count=AsyncMock(return_value=0),  # Simulate no "50 more" button found
#         is_visible=AsyncMock(return_value=False),
#     )
#     mock_page.goto.return_value = None
#     mock_page.wait_for_load_state.return_value = None

#     # Create an instance of the Command class and invoke the method
#     command = Command()
#     content = await command.fetch_all_pages_with_playwright(
#         "https://www.imdb.com/search/title/?title_type=feature&genres=comedy"
#     )

#     # Assertions
#     assert MOCK_HTML in content, "The fetched content does not match the mock HTML"
#     mock_page.goto.assert_called_once_with(
#         "https://www.imdb.com/search/title/?title_type=feature&genres=comedy"
#     )
#     mock_page.wait_for_load_state.assert_called_with("networkidle")
#     mock_page.locator.assert_called_once_with("button.ipc-see-more__button")
#     # Ensure this is awaited in the test
#     await mock_page.locator.return_value.count()


@pytest.mark.asyncio
@patch("movies.management.commands.scrape_movies.Command.fetch_all_pages_with_playwright", AsyncMock(return_value=MOCK_HTML))
async def test_scrape_page():
    from movies.management.commands.scrape_movies import Command

    command = Command()
    movies = await command.scrape_page("https://www.imdb.com/search/title/?title_type=feature&genres=comedy", 1)

    assert len(movies) == 1
    movie = movies[0]
    assert movie["title"] == "Movie Title 1"
    assert movie["year"] == "2023"
    assert movie["duration"] == "120 min"
    assert movie["category"] == "Drama"
    assert movie["rating"] == "8.5"
    assert movie["cast"] == "Actor A, Actor B"
    assert movie["plot"] == "A summary of the movie."


@pytest.mark.asyncio
@patch("movies.management.commands.scrape_movies.Command.scrape_page", AsyncMock(return_value=[
    {
        "title": "Movie Title 1",
        "year": "2023",
        "duration": "120 min",
        "category": "Drama",
        "rating": "8.5",
        "cast": "Actor A, Actor B",
        "plot": "A summary of the movie.",
    },
    {
        "title": "Movie Title 2",
        "year": "2022",
        "duration": "90 min",
        "category": "Comedy",
        "rating": "7.0",
        "cast": "Actor C, Actor D",
        "plot": "Another summary of a different movie.",
    }
]))
async def test_scrape_url():
    from movies.management.commands.scrape_movies import Command

    command = Command()
    movies = await command.scrape_url("http://example.com", 1)

    assert len(movies) == 2

    movie1 = movies[0]
    assert movie1["title"] == "Movie Title 1"
    assert movie1["year"] == "2023"
    assert movie1["duration"] == "120 min"
    assert movie1["category"] == "Drama"
    assert movie1["rating"] == "8.5"
    assert movie1["cast"] == "Actor A, Actor B"
    assert movie1["plot"] == "A summary of the movie."

    movie2 = movies[1]
    assert movie2["title"] == "Movie Title 2"
    assert movie2["year"] == "2022"
    assert movie2["duration"] == "90 min"
    assert movie2["category"] == "Comedy"
    assert movie2["rating"] == "7.0"
    assert movie2["cast"] == "Actor C, Actor D"
    assert movie2["plot"] == "Another summary of a different movie."


@pytest.mark.django_db
@patch("movies.models.Movie.objects.bulk_create")
@patch("movies.models.Movie.objects.bulk_update")
@patch("movies.models.Movie.objects.filter")
def test_save_movies(mock_filter, mock_bulk_update, mock_bulk_create):
    from movies.management.commands.scrape_movies import Command

    command = Command()
    movies = [
        {
            "title": "Movie Title 1",
            "year": 2023,
            "duration": "120 min",
            "category": "Drama",
            "rating": 8.5,
            "cast": "Actor A, Actor B",
            "plot": "A summary of the movie.",
        },
        {
            "title": "Movie Title 2",
            "year": 2022,
            "duration": "90 min",
            "category": "Comedy",
            "rating": 7.5,
            "cast": "Actor C, Actor D",
            "plot": "Another summary.",
        },
    ]

    # Mock the database filter call to return existing movies
    existing_movie = MagicMock(spec=Movie, title="Movie Title 1")
    mock_filter.return_value = [existing_movie]

    # Call the method under test
    command.save_movies(movies)

    # Assert that `Movie.objects.filter` was called with the correct titles
    mock_filter.assert_called_once_with(
        title__in=["Movie Title 1", "Movie Title 2"])

    # Assert `bulk_create` was called with one new movie
    mock_bulk_create.assert_called_once()
    created_movies = mock_bulk_create.call_args[0][0]
    assert len(created_movies) == 1
    assert created_movies[0].title == "Movie Title 2"
    assert created_movies[0].release_year == 2022
    assert created_movies[0].imdb_rating == 7.5

    # Assert `bulk_update` was called with the updated movie fields
    mock_bulk_update.assert_called_once()
    updated_movies = mock_bulk_update.call_args[0][0]
    assert len(updated_movies) == 1
    assert updated_movies[0].title == "Movie Title 1"
    assert updated_movies[0].release_year == 2023
    assert updated_movies[0].imdb_rating == 8.5
    assert updated_movies[0].cast == "Actor A, Actor B"
    assert updated_movies[0].plot_summary == "A summary of the movie."
    assert updated_movies[0].duration == "120 min"
    assert updated_movies[0].category == "Drama"

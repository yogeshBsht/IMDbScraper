# urls.py
from django.urls import path
from movies.views import MovieListView, MovieDetailView

urlpatterns = [
    path('movies/', MovieListView.as_view(), name='list-all-movies'),
    path('movies/<str:title>/', MovieDetailView.as_view(), name='detail-movie'),
]

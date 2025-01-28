# models.py
from django.db import models
from enum import Enum


class Movie(models.Model):
    title = models.CharField(max_length=255, unique=True)
    release_year = models.CharField(max_length=4, null=True, blank=True)
    duration = models.CharField(max_length=10, null=True, blank=True)
    category = models.CharField(max_length=4, null=True, blank=True)
    imdb_rating = models.FloatField(null=True, blank=True)
    director = models.TextField(null=True, blank=True)
    cast = models.TextField(null=True, blank=True)
    plot_summary = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title


class Genre(Enum):
    COMEDY = "comedy"
    ACTION = "action"
    DRAMA = "drama"
    HORROR = "horror"


class TitleType(Enum):
    FEATURE = "feature"
    TV_SERIES = "tv_series"
    SHORT = "short"

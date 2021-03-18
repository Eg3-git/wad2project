from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    producer = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Genre(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    name = models.CharField(max_length=128, unique=True)
    release_date = models.DateField(default="Unknown")
    actors = models.CharField(max_length=256)
    producer = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    trailer = models.URLField(max_length=128)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Movie, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class Rating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    def __str__(self):
        return "Movie: {}, Score: {}.".format(self.movie.name, self.rating)

class Comment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    text = models.TextField(max_length=1024)
    time_posted = models.DateField(default="Unknown")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)

    def __str__(self):
        return self.text

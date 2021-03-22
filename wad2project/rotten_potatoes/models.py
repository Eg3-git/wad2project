from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to="profile_images", blank=True)
    description = models.TextField(max_length=1024, default="")

    #boolean flag for identifying producers
    producer = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Movie(models.Model):
    name = models.CharField(max_length=128)
    release_date = models.DateField(null=True)
    actors = models.CharField(max_length=256)
    genre = models.CharField(max_length=256)
    # Producer ForeignKey
    producer = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    trailer = models.URLField(max_length=128)
    description = models.TextField(max_length=1024)
    cover = models.ImageField(upload_to="movie_images", blank=True)
    upload_date = models.DateField()
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        # Produce slug from name, then save
        self.slug = slugify(self.name)
        self.upload_date = datetime.now()
        super(Movie, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class Rating(models.Model):
    # Movie and User Foreign Keys
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    rating = models.IntegerField(default=0)

    def __str__(self):
        return "Movie: {}, Score: {}.".format(self.movie.name, self.rating)

class Comment(models.Model):
    # UserProfile Foreign Key
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    text = models.TextField(max_length=1024)
    time_posted = models.DateField()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)

    def __str__(self):
        self.time_posted = datetime.now()
        return self.text

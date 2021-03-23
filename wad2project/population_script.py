import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wad2project.settings')

import django
django.setup()
from rotten_potatoes.models import *
from django.contrib.auth.models import User
from datetime import datetime

def populate():
    # Rating objects list.
    ratings = [
        [
            {'rating': 2},
            {'rating': 0},
            {'rating': 1}
        ],
        [
            {'rating': 4},
            {'rating': 3}
        ],
        [
            {'rating': 3},
            {'rating': 5}
        ],
        [
            {'rating': 5},
            {'rating': 1},
            {'rating': 3}
        ]
    ]

    # Comment objects list.
    comments = [
        [
            {'text': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec vitae.',
             'time_posted': datetime.now()},
            {'text': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas at nulla luctus, pulvinar felis non.',
             'time_posted': datetime.now()}
        ],
        [
            {'text': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
             'time_posted': datetime.now()},
            {'text': 'Lorem ipsum dolor sit.',
             'time_posted': datetime.now()}
        ],
        [
            {'text': 'Lorem ipsum dolor sit amet, consectetur adipiscing.',
             'time_posted': datetime.now()}
        ],
        [
            {'text': 'Lorem ipsum dolor sit amet.',
             'time_posted': datetime.now()}
        ]
    ]

    # Movie objects list.
    movies = [
        [
            {'name': 'Taken',
             'release_date': datetime.now(),
             'actors': 'Liam Neeson, Maggie Grace',
             'genre': 'Thriller',
             'trailer': 'https://www.youtube.com/watch?v=uPJVJBm9TPA&t=3s',
             'upload_date': datetime.now(),
             'ratings': ratings[0],
             'comments': comments[0]
            },
            {'name': 'News of the World',
             'release_date': datetime.now(),
             'actors': 'Tom Hanks',
             'genre': 'Western',
             'trailer': 'https://www.youtube.com/watch?v=zTZDb_iKooI',
             'upload_date': datetime.now(),
             'ratings': ratings[1],
             'comments': comments[1]
            }
        ],
        [
            {'name': 'The Ballad of Buster Scruggs',
             'release_date': datetime.now(),
             'actors': 'Tim Blake Nelson, James Franco, Zoe Kazan, Liam Neeson',
             'genre': 'Western',
             'trailer': 'https://www.youtube.com/watch?v=_2PyxzSH1HM',
             'upload_date': datetime.now(),
             'ratings': ratings[2],
             'comments': comments[2]
           }
         ],
         [
            {'name': 'The Lord of the Rings: The Fellowship of the Ring',
             'release_date': datetime.now(),
             'actors': 'Elijah Wood, Ian Mckellen',
             'genre': 'Fantasy',
             'trailer': 'https://www.youtube.com/watch?v=V75dMMIW2B4',
             'upload_date': datetime.now(),
             'ratings': ratings[3],
             'comments': comments[3]
            }
        ]
    ]

    # User objects list.
    users = [
        {'username': 'Chris',
         'password': 'djangoProject',
         'producer': False},
        {'username': 'Michael',
         'password': 'djangoProject',
         'producer': False},
        {'username': 'Tom',
         'password': 'djangoProject',
         'producer': False},
        {'username': 'John',
         'password': 'djangoProject',
         'producer': True,
         'movies': movies[0]},
         {'username': 'Trevor',
          'password': 'djangoProject',
          'producer': True,
          'movies': movies[1]},
         {'username': 'Franklin',
          'password': 'djangoProject',
          'producer': True,
          'movies': movies[2]}
    ]

    for user in users:
        user_p = add_user(user['username'], user['password'], user['producer'])
        # If the user is a producer, add his movies to the database.
        if user['producer']:
            for current_movie in user['movies']:
                movie = add_movie(current_movie['name'], current_movie['release_date'], current_movie['actors'], current_movie['genre'], current_movie['trailer'], current_movie['upload_date'], user_p)
                # Add ratings and comments associated with this movie to the database.
                for rating in current_movie['ratings']:
                    add_rating(user_p, movie, rating['rating'])
                for comment in current_movie['comments']:
                    add_comment(user_p, movie, comment['time_posted'], comment['text'])

# Helper functions

# Create user and a corresponding user profile, return the user profile.
def add_user(username, password, producer):
    user = User.objects.get_or_create(username=username)[0]
    user.set_password(password)
    user.save()
    user_profile = UserProfile.objects.get_or_create(user=user)[0]
    user_profile.producer = producer
    user_profile.save()
    return user_profile

def add_movie(name, rdate, actors, genre, trailer, udate, producer):
    movie = Movie.objects.get_or_create(name=name, producer=producer)[0]
    movie.release_date = rdate
    movie.actors = actors
    movie.genre = genre
    movie.trailer = trailer
    movie.upload_date = udate
    movie.producer = producer
    movie.save()
    return movie

def add_rating(user_profile, movie, score):
    rating = Rating.objects.get_or_create(movie=movie, user=user_profile, rating=score)[0]
    rating.save()
    return rating

def add_comment(user, movie, tposted, text):
    comment = Comment.objects.get_or_create(user=user, text=text, movie=movie, time_posted=tposted)[0]
    comment.save()
    return comment

if __name__ == '__main__':
    print("Starting population script...")
    populate()

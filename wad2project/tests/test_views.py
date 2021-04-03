from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from rotten_potatoes.models import *


class TestIndexViewEmptyDatabase(TestCase):

    def test_index_GET_with_empty_database(self):
        client = Client()
        response = client.get(reverse('index'))

        # Check if page loads with status code 200
        self.assertEquals(response.status_code, 200)
        # Check if correct template selected
        self.assertTemplateUsed(response, 'rotten_potatoes/index.html')
        # If database is empty, this messages should be displayed
        self.assertContains(response, "Sorry, there are no movies in the database.")
        self.assertContains(response, "There are no recently added movies.")
        self.assertContains(response, "No favorite movie for this year.")


class TestIndexViewNotEmptyDatabase(TestCase):

    def setUp(self):
        self.client = Client()
        self.index_url = reverse('index')
        self.test_profile = UserProfile.objects.create(user=User.objects.create_user(username="test_profile",
                                                                                     password="123"))

    def create_movie(self, name, upload_date):
        return Movie.objects.create(name=name, producer=self.test_profile, upload_date=upload_date)

    def test_index_GET_with_non_empty_database(self):
        # Create test movie
        self.create_movie(name="Test Movie", upload_date=datetime.now())

        response = self.client.get(self.index_url)
        # Check if page loads with status code 200
        self.assertEquals(response.status_code, 200)

        # Check if queries are not empty
        self.assertQuerysetEqual(response.context['top_movies'], ['<Movie: Test Movie>'])
        self.assertQuerysetEqual(response.context['recently_added'], ['<Movie: Test Movie>'])
        self.assertQuerysetEqual(response.context['this_years_favorite'], ['<Movie: Test Movie>'])

    def test_index_GET_with_empty_recently_added_movies(self):
        # Create test movie with upload -15 days in past
        self.create_movie(name="Test Not Recent", upload_date=datetime.now() - timedelta(days=15))
        response = self.client.get(self.index_url)

        # Check if page loads with status code 200
        self.assertEquals(response.status_code, 200)

        # Check if recently_added query is empty with correct message
        self.assertContains(response, "There are no recently added movies.")
        self.assertQuerysetEqual(response.context['recently_added'], [])

    def test_index_GET_with_empty_this_years_favorite_movie(self):
        # Create movie with upload date 400 days in past
        self.create_movie(name="Past Movie", upload_date=datetime.now() - timedelta(days=400))
        # Create movie with upload date 400 days in future
        self.create_movie(name="Future Movie", upload_date=datetime.now() + timedelta(days=400))

        response = self.client.get(self.index_url)
        # Check if page loads with status code 200
        self.assertEquals(response.status_code, 200)

        # Check if this_years_favorite query set is empty with correct message
        self.assertContains(response, "No favorite movie for this year.")
        self.assertQuerysetEqual(response.context['this_years_favorite'], [])


class TestAboutView(TestCase):

    def test_about_GET_uses_correct_template(self):
        client = Client()

        response = client.get(reverse('rotten_potatoes:about'))

        # Check if page loads with status code 200
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/about.html")


class TestMovieView(TestCase):

    def setUp(self):
        self.client = Client()
        self.movie_url = reverse("rotten_potatoes:movie", args=["test-movie"])
        self.test_profile = UserProfile.objects.create(user=User.objects.create_user(username="test_profile",
                                                                                     password="123"))
        self.test_movie = Movie.objects.create(name="Test Movie", producer=self.test_profile)

    def test_movie_GET_uses_correct_template(self):
        response = self.client.get(self.movie_url)

        # Check if page loads with status code 200
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/movie.html")

    def test_movie_GET_displays_correct_data(self):
        # Set values for movie obj
        self.test_movie.release_date = "1111-11-11"
        self.test_movie.actors = "Test Actor"
        self.test_movie.genre = "Test Genre"
        self.test_movie.description = "Test Description"
        self.test_movie.
        response = self.client.get(self.movie_url)
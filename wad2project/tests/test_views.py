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

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user)

    def create_movie(self, name, upload_date, release_date=datetime.now()):
        return Movie.objects.create(name=name, producer=self.test_profile, upload_date=upload_date,
                                    release_date=release_date)

    def test_index_GET_with_non_empty_database(self):
        # Create test movie
        self.create_movie(name="Test Movie", upload_date=datetime.now())

        response = self.client.get(self.index_url)
        # Check if page loads with status code 200
        self.assertEquals(response.status_code, 200)

        # Check if queries are not empty
        self.assertQuerysetEqual(response.context['top_movies'], ['<Movie: Test Movie>'])
        self.assertQuerysetEqual(response.context['recently_added'], ['<Movie: Test Movie>'])
        self.assertEquals(response.context['this_years_favorite'].name, 'Test Movie')

    def test_index_GET_with_empty_recently_added_movies(self):
        # Create test movie with upload -15 days in past
        upload_date_not_recent = datetime.now() - timedelta(days=15)
        self.create_movie(name="Not Recent Movie", upload_date=upload_date_not_recent)
        response = self.client.get(self.index_url)

        # Check if page loads with status code 200
        self.assertEquals(response.status_code, 200)

        # Check if recently_added query is empty with correct message
        self.assertContains(response, "There are no recently added movies.")
        self.assertQuerysetEqual(response.context['recently_added'], [])

    def test_index_GET_with_empty_this_years_favorite_movie(self):
        # Create movie with upload date 400 days in past
        upload_date_past = datetime.now() - timedelta(days=400)
        self.create_movie(name="Past Movie", upload_date=upload_date_past)
        # Create movie with upload date 400 days in future
        upload_date_future = datetime.now() + timedelta(days=400)
        self.create_movie(name="Future Movie", upload_date=upload_date_future)

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

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user)

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
        upload_date = datetime.now()
        self.test_movie.upload_date = upload_date
        self.test_movie.save()

        # Create comment associated with the movie
        comment = Comment.objects.create(movie=self.test_movie, user=self.test_profile,
                                         time_posted=datetime.now(), text="Test Comment")

        # Create rating associated with the movie
        rating = Rating.objects.create(movie=self.test_movie, user=self.test_profile, rating=5)

        response = self.client.get(self.movie_url)

        # Check if page loads with status code 200
        self.assertEquals(response.status_code, 200)

        # Check if correct object is queried (instance of Movie)
        self.assertIsInstance(response.context['movie'], Movie)

        # Compare each field with expected value
        self.assertEquals(response.context['movie'].name, 'Test Movie')
        self.assertEquals(response.context['movie'].producer, self.test_profile)
        self.assertEquals(str(response.context['movie'].release_date), '1111-11-11')
        self.assertEquals(response.context['movie'].genre, 'Test Genre')
        self.assertEquals(response.context['movie'].actors, 'Test Actor')
        self.assertEquals(response.context['movie'].description, "Test Description")
        self.assertEquals(response.context['movie'].upload_date, upload_date.date())
        self.assertQuerysetEqual(response.context['comments'], ['<Comment: Test Comment>'])
        self.assertEquals(response.context['movie'].avg_rating, 5.0)
        self.assertEquals(response.context['movie'].num_of_ratings, 1)

        # Check if data is displayed correctly
        self.assertContains(response, "Test Movie")  # Movie name
        self.assertContains(response, str(self.test_profile.user.username))  # Producers name
        self.assertContains(response, 'Release Date = Nov. 11, 1111')  # Release date
        self.assertContains(response, 'Actors = Test Actor')  # List of actors
        self.assertContains(response, 'Genre = Test Genre')  # Movie genre
        self.assertContains(response, 'Description = Test Description')  # Description
        self.assertContains(response, "Average Rating = " + "5")  # Average rating
        self.assertContains(response, "Number Of Ratings = " + "1")  # Num of ratings
        self.assertContains(response, "Test Comment")  # Comments


class TestEditMovieVies(TestCase):

    def setUp(self):
        self.client = Client()
        self.edit_movie_url = reverse("rotten_potatoes:edit_movie", args=["test-movie"])

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user)

    def create_movie(self, name, upload_date=datetime.now(), release_date=datetime.now()):
        return Movie.objects.create(name=name, producer=self.test_profile, upload_date=upload_date,
                                    release_date=release_date)

    def test_edit_GET_without_existing_movie_should_redirect_to_index_with_message(self):
        self.client.login(username="test_profile", password="123")      # Login client
        response = self.client.get(self.edit_movie_url, follow=True)    # Follow the redirect

        # Check that response should still be 200
        self.assertEquals(response.status_code, 200)

        # Check we got redirected to index
        self.assertTemplateUsed(response, 'rotten_potatoes/index.html')

        # Check that correct message displayed
        self.assertContains(response, "Sorry, movie you tried to access does not exists")

    def test_edit_GET_contains_preexisting_data(self):
        self.client.login(username="test_profile", password="123")  # Login client

        test_movie = self.create_movie(name="Test Movie")
        test_movie.release_date = "1111-11-11"
        test_movie.actors = "Test Actor"
        test_movie.genre = "Test Genre"
        test_movie.description = "Test Description"
        test_movie.save()

        response = self.client.get(self.edit_movie_url, follow=True)  # Follow the redirect

        form = response.context['form']
        clean_data = form.cleaned_data()
        print(clean_data)

        # Check form is valid
        self.assertTrue(form.is_valid())

        # Check form contains preexisting data
        self.assertEquals(form['name'], 'Test Movie')
        self.assertEquals(form['release_date'], '1111-11-11')
        self.assertEquals(form['actors'], 'Test Actor')
        self.assertEquals(form['genre'], 'Test Genre')
        self.assertEquals(form['description'], 'Test Description')
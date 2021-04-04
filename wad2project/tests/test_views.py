from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse

from rotten_potatoes.forms import *
from rotten_potatoes.models import *
from rotten_potatoes.views import *


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

    def create_movie(self, name, upload_date=datetime.now(), release_date=datetime.now()):
        return Movie.objects.create(name=name, producer=self.test_profile, upload_date=upload_date,
                                    release_date=release_date)

    def test_index_GET_with_non_empty_database(self):
        # Create test movie
        self.create_movie(name="Test Movie")

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
        Comment.objects.create(movie=self.test_movie, user=self.test_profile,
                               time_posted=datetime.now(), text="Test Comment")

        # Create rating associated with the movie
        Rating.objects.create(movie=self.test_movie, user=self.test_profile, rating=5)

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
        self.assertEquals(response.context['movie'].avg_rating, 5)
        self.assertEquals(response.context['movie'].num_of_ratings, 1)
        self.assertEquals(response.context['movie'].trailer, "")

        # Check if data is displayed correctly
        self.assertContains(response, "Test Movie")                             # Movie name
        self.assertContains(response, str(self.test_profile.user.username))     # Producers name
        self.assertContains(response, 'Release Date: Nov. 11, 1111')            # Release date
        self.assertContains(response, 'Actors: Test Actor')                     # List of actors
        self.assertContains(response, 'Genre: Test Genre')                      # Movie genre
        self.assertContains(response, 'Test Description')                       # Description
        self.assertContains(response, "Rating: 5")                              # Average rating
        self.assertContains(response, "Number of Ratings: 1")                   # Num of ratings
        self.assertContains(response, "Test Comment")                           # Comments


class TestEditMovieVies(TestCase):

    def setUp(self):
        self.client = Client()
        self.edit_movie_url = reverse("rotten_potatoes:edit_movie", args=["test-movie"])

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user)

    def create_movie(self, name, upload_date=datetime.now(), release_date=datetime.now().date()):
        return Movie.objects.create(name=name, producer=self.test_profile, upload_date=upload_date,
                                    release_date=release_date)

    def test_edit_movie_GET_without_existing_movie_should_redirect_to_index_with_message(self):
        self.client.login(username="test_profile", password="123")    # Login client
        response = self.client.get(self.edit_movie_url, follow=True)  # Follow the redirect

        # Check that response should still be 200
        self.assertEquals(response.status_code, 200)

        # Check we got redirected to index
        self.assertTemplateUsed(response, 'rotten_potatoes/index.html')

        # Check that correct message displayed
        self.assertContains(response, "Sorry, movie you tried to access does not exists")

    def test_edit_movie_POST_changes_movie_data_and_redirects_correctly(self):
        self.client.login(username="test_profile", password="123")  # Login client

        # Create movie with empty fields
        test_movie = self.create_movie(name="Test Movie Edit")
        test_movie.actors = ""
        test_movie.genre = ""
        test_movie.trailer = ""
        test_movie.description = ""
        test_movie.save()

        response = self.client.post(reverse("rotten_potatoes:edit_movie", args=[test_movie.slug]), data={
            "name": "Test Movie Edit",
            "release_date": "1111-11-11",
            "actors": "Test Actor",
            "trailer": "https://www.google.com/",
            "genre": "Action",
            "description": "Test Description"
        }, follow=True)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/movie.html")

        # Check data changed correctly
        self.assertTrue(test_movie.name == "Test Movie Edit")
        self.assertTrue(test_movie.release_date == "1111-11-11")
        self.assertTrue(test_movie.actors == "Test Actor")
        self.assertTrue(test_movie.trailer == "https://www.google.com/")
        self.assertTrue(test_movie.genre == "Action")
        self.assertTrue(test_movie.description == "Test Description")


class TestAddMovieView(TestCase):

    def setUp(self):
        self.client = Client()
        self.add_movie_url = reverse("rotten_potatoes:add_movie")

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user, producer=True)

    def test_add_movie_GET_uses_correct_template(self):
        self.client.login(username="test_profile", password="123")  # Login client

        response = self.client.get(self.add_movie_url)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/addmovie.html")

    def test_add_movie_GET_redirects_user_who_is_not_producer(self):
        # Create user who is not producer
        usr = User.objects.create_user(username="not_producer")
        usr.set_password("123")
        usr.save()

        usr_profile = UserProfile.objects.create(user=usr, producer=False)

        self.client.login(username="not_producer", password="123")  # Login client

        response = self.client.get(self.add_movie_url, follow=True)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/index.html")

        # Check if correct message contained
        self.assertContains(response, "Sorry, you can not add a movie")
        
    def test_add_movie_POST_shows_message_when_unique_constraint_violated(self):
        self.client.login(username="test_profile", password="123")  # Login client

        # Create movie
        Movie.objects.create(name="Test Movie", producer=self.test_profile)

        # Data to be sent via POST
        data = {
            "name": "Test Movie",
        }

        response = self.client.post(self.add_movie_url, data=data, follow=True)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/addmovie.html")

        # Check if correct message contained
        self.assertContains(response, "Movie with this name already exists. Try movie name + release year.")

    def test_add_movie_POST_creates_movie_correctly(self):
        self.client.login(username="test_profile", password="123")  # Login client

        data = {
            "name": "Test Movie",
            "release_date": datetime.now().date(),
            "actors": "Test Actor",
            "trailer": "",
            "genre": "Action",
            "description": "Test Description"
        }

        response = self.client.post(self.add_movie_url, data=data, follow=True)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if redirected to correct newly create movie page
        self.assertTemplateUsed(response, "rotten_potatoes/movie.html")

        # Check if movie with such field created
        obj = Movie.objects.get(slug="test-movie")

        self.assertTrue(obj.name == data["name"])
        self.assertTrue(obj.release_date == data["release_date"])
        self.assertTrue(obj.actors == data["actors"])
        self.assertTrue(obj.trailer == data["trailer"])
        self.assertTrue(obj.genre == data["genre"])
        self.assertTrue(obj.description == data["description"])


class TestAddRatingView(TestCase):

    def setUp(self):
        self.client = Client()
        self.rate_movie_url = reverse("rotten_potatoes:rate_movie", args=["test-movie"])

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user, producer=True)

    def test_rate_movie_GET_owner_can_not_rate_own_movie(self):
        self.client.login(username="test_profile", password="123")

        response = self.client.get(self.rate_movie_url, follow=True)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/movie.html")

        # Check if correct message contained
        self.assertContains(response, "You can not rate your own movie")

    def test_rate_movie_POST_creates_rating_correctly(self):
        # Create user who is not producer
        usr = User.objects.create_user(username="not_producer")
        usr.set_password("123")
        usr.save()

        UserProfile.objects.create(user=usr, producer=False)

        self.client.login(username="not_producer", password="123")  # Login client

        response = self.client.post(self.rate_movie_url, data={"rating": 5}, follow=True)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if redirected to correct template
        self.assertTemplateUsed(response, "rotten_potatoes/movie.html")

        # Check if rating is contained
        self.assertContains(response, "Number of Ratings: 1")
        self.assertContains(response, "Rating: 5")


class TestAccountView(TestCase):

    def setUp(self):
        self.client = Client()
        self.account_url = reverse("rotten_potatoes:account")

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user, producer=True)

    def test_account_GET_uses_correct_template(self):
        self.client.login(username="test_profile", password="123")

        response = self.client.get(self.account_url)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/account.html")

    def test_account_GET_displays_correct_data(self):
        self.client.login(username="test_profile", password="123")

        # Create two movie associated with test profile
        test_movie1 = Movie.objects.create(name="Test Movie1", producer=self.test_profile)
        test_movie2 = Movie.objects.create(name="Test Movie2", producer=self.test_profile)

        response = self.client.get(self.account_url)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if data displayed correctly
        self.assertContains(response, self.test_profile.user.username)
        self.assertQuerysetEqual(response.context["movies"], ['<Movie: Test Movie1>', '<Movie: Test Movie2>'], ordered=False)


class TestEditAccountView(TestCase):

    def setUp(self):
        self.client = Client()
        self.edit_account_url = reverse("rotten_potatoes:edit_account")

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user, description="")

    def test_edit_account_GET_uses_correct_template(self):
        self.client.login(username="test_profile", password="123")

        response = self.client.get(self.edit_account_url)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/editaccount.html")

    def test_edit_account_POST_changes_account_data_and_redirects_correctly(self):
        self.client.login(username="test_profile", password="123")  # Login client

        data = {
            "profile_pic": "",
            "description": "Test Description"
        }

        response = self.client.post(self.edit_account_url, data=data, follow=True)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used after redirect
        self.assertTemplateUsed(response, "rotten_potatoes/account.html")

        # Check data changed correctly
        self.assertTrue(self.test_profile.profile_pic == "profile_images/default.png")  # If no file provided should set default picture
        self.assertTrue(self.test_profile.description == "Test Description")


class TestAddCommentView(TestCase):

    def setUp(self):
        self.client = Client()
        self.comment_url = reverse('rotten_potatoes:add_comment', args=["test-movie"])

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user)

        self.test_movie = Movie.objects.create(name="Test Movie", producer=self.test_profile)

    def test_add_comment_GET_uses_correct_template(self):
        self.client.login(username="test_profile", password="123")

        response = self.client.get(self.comment_url)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/addcomment.html")

    def test_add_comment_GET_displays_correct_data(self):
        self.client.login(username="test_profile", password="123")

        response = self.client.get(self.comment_url)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check correct data is displayed
        self.assertContains(response, "Add Comment To: Test Movie")

    def test_add_comment_POST_adds_comment_and_redirects_to_movie_page_correctly(self):
        self.client.login(username="test_profile", password="123")

        data = {
            "text": "Test Comment",
            "user": self.test_profile,
            "movie": self.test_movie
        }

        response = self.client.post(self.comment_url, data=data, follow=True)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check we got redirected correctly
        self.assertTemplateUsed(response, "rotten_potatoes/movie.html")

        # Check comment is displayed correctly
        self.assertContains(response, self.test_profile.user.username)
        self.assertContains(response, "Test Comment")


class TestDeleteCommentView(TestCase):

    def setUp(self):
        self.client = Client()

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user)

        self.test_movie = Movie.objects.create(name="Test Movie", producer=self.test_profile)
        self.test_comment = Comment.objects.create(user=self.test_profile, movie=self.test_movie,
                                                   text="Test Comment", time_posted=datetime.now())

    def test_delete_comment_GET_redirects_user_who_is_not_owner_of_comment(self):
        # Create test user
        user = User.objects.create_user(username="not_owner")
        user.set_password("123")
        user.save()

        test_profile_not_owner = UserProfile.objects.create(user=user)

        self.client.login(username="not_owner", password="123")
        response = self.client.get(reverse("rotten_potatoes:movie", args=["test-movie"]), follow=True)

        delete_comment(response.wsgi_request, self.test_movie.slug, self.test_comment.pk)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used after redirect
        self.assertTemplateUsed(response, "rotten_potatoes/movie.html")

        # Check correct message displayed
        self.assertContains(response, "You can not delete this comment")

    def test_delete_comment_GET_deletes_comment_correctly(self):
        self.client.login(username="test_profile", password="123")  # Login client

        response = self.client.get(reverse("rotten_potatoes:movie", args=["test-movie"]), follow=True)

        delete_comment(response.wsgi_request, self.test_movie.slug, self.test_comment.pk)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used after redirect
        self.assertTemplateUsed(response, "rotten_potatoes/movie.html")

        # Check comment is deleted
        self.assertNotContains(response, "Test Comment")


class TestDeleteMovieView(TestCase):
    def setUp(self):
        self.client = Client()

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user)

        self.test_movie = Movie.objects.create(name="Test Movie", producer=self.test_profile)

    def test_delete_movie_GET_redirects_user_who_is_not_owner_of_the_movie(self):
        # Create test user
        user = User.objects.create_user(username="not_owner")
        user.set_password("123")
        user.save()

        UserProfile.objects.create(user=user)

        self.client.login(username="not_owner", password="123")

        response = self.client.get(reverse("rotten_potatoes:movie", args=["test-movie"]), follow=True)

        # attempt deleting movie
        delete_movie(response.wsgi_request, "test-movie")

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used after redirect
        self.assertTemplateUsed(response, "rotten_potatoes/movie.html")

        # Check correct message displayed
        self.assertContains(response, "You are not permitted to delete this movie")

    def test_delete_movie_GET_deletes_comment_correctly(self):
        self.client.login(username="test_profile", password="123")  # Login client

        response = self.client.get(reverse("rotten_potatoes:movie", args=["test-movie"]), follow=True)

        delete_movie(response.wsgi_request, self.test_movie.slug)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used after redirect
        self.assertTemplateUsed(response, "rotten_potatoes/index.html")

        # Check comment is deleted
        self.assertContains(response, "You have successfully deleted the movie.")


class TestRatingsView(TestCase):

    def setUp(self):
        self.client = Client()
        self.ratings_url = reverse("rotten_potatoes:ratings")

        user = User.objects.create_user(username="test_profile")
        user.set_password("123")
        user.save()

        self.test_profile = UserProfile.objects.create(user=user)

        self.test_movie1 = Movie.objects.create(name="Test Movie1", producer=self.test_profile, genre="Action")
        self.test_movie2 = Movie.objects.create(name="Test Movie2", producer=self.test_profile, genre="Drama")

    def test_ratings_GET_uses_correct_template(self):
        response = self.client.get(self.ratings_url)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct template is used
        self.assertTemplateUsed(response, "rotten_potatoes/ratings.html")

    def test_ratings_GET_uses_correct_data(self):
        response = self.client.get(self.ratings_url)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct data is displayed
        self.assertContains(response, "Test Movie1")
        self.assertContains(response, "Test Movie2")

    def test_ratings_POST_filters_correctly_for_genre(self):
        response = self.client.post(self.ratings_url, data={"genre": "Action", "sort_by": "-avg_rating"})

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check if correct data is displayed
        self.assertContains(response, "Test Movie1")
        self.assertNotContains(response, "Test Movie2")

    def test_ratings_POST_orders_correctly_by_sort_by(self):

        test_movie3 = Movie.objects.create(name="Test Movie3", producer=self.test_profile, genre="Action")

        response = self.client.post(self.ratings_url, data={"genre": "Action", "sort_by": "-avg_rating"})

        # Create rating for each movie
        Rating.objects.create(user=self.test_profile, movie=self.test_movie1, rating=5)
        Rating.objects.create(user=self.test_profile, movie=test_movie3, rating=3)

        # Check status code is OK
        self.assertEquals(response.status_code, 200)

        # Check correct query set is given
        self.assertQuerysetEqual(response.context["movie_list"], ['<Movie: Test Movie1>', '<Movie: Test Movie3>'],
                                 ordered=False)
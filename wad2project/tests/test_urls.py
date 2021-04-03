from django.test import TestCase
from django.urls import resolve
from rotten_potatoes.views import *


class TestUrls(TestCase):

    def test_index_url_is_resolved(self):
        url = reverse('index')
        self.assertEquals(resolve(url).func, index)

    def test_about_url_is_resolved(self):
        url = reverse('rotten_potatoes:about')
        self.assertEquals(resolve(url).func, about)

    def test_register_url_is_resolved(self):
        url = reverse('rotten_potatoes:register')
        self.assertEquals(resolve(url).func, register)

    def test_login_url_is_resolved(self):
        url = reverse('rotten_potatoes:login')
        self.assertEquals(resolve(url).func, user_login)

    def test_logout_url_is_resolved(self):
        url = reverse('rotten_potatoes:logout')
        self.assertEquals(resolve(url).func, user_logout)

    def test_movie_url_is_resolved(self):
        url = reverse('rotten_potatoes:movie', args=["slug"])
        self.assertEquals(resolve(url).func, movie)

    def test_edit_movie_url_is_resolved(self):
        url = reverse('rotten_potatoes:edit_movie', args=["slug"])
        self.assertEquals(resolve(url).func, edit_movie)

    def test_add_comment_url_is_resolved(self):
        url = reverse('rotten_potatoes:add_comment', args=["slug"])
        self.assertEquals(resolve(url).func, add_comment)

    def test_rate_movie_url_is_resolved(self):
        url = reverse('rotten_potatoes:rate_movie', args=["slug"])
        self.assertEquals(resolve(url).func, rate_movie)

    def test_add_movie_url_is_resolved(self):
        url = reverse('rotten_potatoes:add_movie')
        self.assertEquals(resolve(url).func, add_movie)

    def test_account_url_is_resolved(self):
        url = reverse('rotten_potatoes:account')
        self.assertEquals(resolve(url).func, account)

    def test_edit_account_url_is_resolved(self):
        url = reverse('rotten_potatoes:edit_account')
        self.assertEquals(resolve(url).func, edit_account)

    def test_ratings_url_is_resolved(self):
        url = reverse('rotten_potatoes:ratings')
        self.assertEquals(resolve(url).func, ratings)
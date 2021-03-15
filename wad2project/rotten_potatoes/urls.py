from django.urls import path
from rotten_potatoes import views


app_name = 'rotten_potatoes'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('<slug:movie_name_slug>/', views.movie, name='movie'),
    path('<slug:movie_name_slug>/edit/', views.edit_movie, name='edit_movie'),
    path('<slug:movie_name_slug>/addcomment/', views.add_comment, name='add_comment'),
    path('<slug:movie_name_slug>/ratemovie/', views.rate_movie, name='rate_movie'),
    path('addmovie/', views.add_movie, name='add_movie'),
    path('account/', views.account, name='account'),
    path('account/edit/', views.edit_account, name='edit_account'),
    path('ratings/', views.ratings, name='ratings'),
    ]
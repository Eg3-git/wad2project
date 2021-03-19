from django.db.models import Count, Avg
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from rotten_potatoes.models import *
from rotten_potatoes.forms import *
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from datetime import datetime


def index(request):
    # Query the top 5 movies
    top_movies = Movie.object.annotate(avg_rating=Avg('rating__rating')).order_by('-avg_rating')[:5]

    # Query recently added movies -> requires field in movie model to track when added
    # Get movies which were uploaded in past 14 days
    recently_added = Movie.object.filter(upload_date__gte=datetime.date.today() - 14)

    # Change this weeks favorite to this years favorite #
    this_years_favorite = Movie.object.filter(release_date__gte='2021-01-01'). \
        annotate(avg_rating=Avg('rating__rating')).order_by('-avg_rating')[0]

    context_dictionary = {
        "top_movies": top_movies,
        "recently_added": recently_added,
        "this_years_favorite": this_years_favorite,
    }

    return render(request, "rotten_potatoes/index.html", context_dictionary)


def about(request):
    return render(request, "rotten_potatoes/about.html")


def register(request):
    registered = False

    if request.method == "POST":
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True

        else:
            print(user_form.errors, profile_form.errors)

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(request, 'rotten_potatoes/register.html', context={'user_form': user_form,
                                                                     'profile_form': profile_form,
                                                                     'registered': registered})


def user_login(request):
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        # We use request.POST.get('<variable>') as opposed
        # to request.POST['<variable>'], because the
        # request.POST.get('<variable>') returns None if the
        # value does not exist, while request.POST['<variable>']
        # will raise a KeyError exception.
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)
        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return redirect(reverse('rotten_potatoes:index'))
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rotten Potatoes account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print(f"Invalid login details: {username}, {password}")
            return HttpResponse("Invalid login details supplied.")
    # The request is not a HTTP POST, so display the login form
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'rotten_potatoes/login.html')


@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)
    # Take the user back to the homepage.
    return redirect(reverse('rotten_potatoes:index'))


def movie(request, movie_name_slug):
    context_dictionary = get_movie_context(movie_name_slug)

    # Render movie page with context dict. information passed
    return render(request, "rotten_potatoes/movie.html", context_dictionary)


@login_required
def edit_movie(request, movie_name_slug):
    form = EditMovieForm()
    context_dictionary = {}
    initial_dict = {}

    # Get movie from the database, if not present return HttpResponse
    try:
        movie_obj = Movie.object.get(slug=movie_name_slug)
    except movie_obj.DoesNotExist:
        return HttpResponse("Fatal error, could not find " + movie_name_slug + " in the database")

    # Check if user is not the movie producer and admin
    if request.user.pk() != movie_obj.user.pk() and not request.user.is_superuser():
        print("Permission to edit denied.")
        redirect("/rotten_potatoes/")

    if request.method == "GET":
        # Fill initial dictionary with pre-existing values
        initial_dict["name"] = movie_obj.name
        initial_dict["release_date"] = movie_obj.release_date
        initial_dict["actors"] = movie_obj.actors
        initial_dict["producer"] = movie_obj.producer
        initial_dict["trailer"] = movie_obj.trailer
        initial_dict["genre"] = movie_obj.genre
        initial_dict["description"] = movie_obj.description

        # Get from with initial values set to pre-existing movie data
        form = EditMovieForm(initial=initial_dict)

        return render(request, "rotten_potatoes/edit.html", {"form": form})

    if request.method == "POST":
        form = EditMovieForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            context_dictionary = get_movie_context(movie_name_slug)

            return render(request, "rotten_potatoes/movie.html", context_dictionary)

        else:
            print(form.errors)
            return HttpResponse(form.errors)


@login_required
def add_comment(request, movie_name_slug):
    form = AddCommentForm()

    if request.method == "POST":
        form = AddCommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.movie = Movie.object.get(slug=movie_name_slug)
            comment.save()

            return movie(request, movie_name_slug)
        else:
            print(form.errors)

    return render(request, "rotten_potatoes/addcomment.html", {"form": form})


@login_required
def rate_movie(request, movie_name_slug):
    pass


@login_required
def add_movie(request):
    form = MovieForm()

    if request.method == "POST":
        if not request.user.producer:
            return redirect('/rotten_potatoes/')

        form = MovieForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return redirect('/rotten_potatoes/')
        else:
            print(form.errors)

    return render(request, 'rotten_potatoes/addmovie.html', {"form": form})


@login_required
def account(request):
    pass


@login_required
def edit_account(request):
    pass


def ratings(request):
    pass


def get_movie_context(movie_name_slug):
    context_dictionary = {}
    try:
        # Get movie object to get details
        movie_obj = Movie.object.get(slug=movie_name_slug)
        # Get average rating and number of ratings
        movie_obj = movie_obj.annotate(avg_rating=Avg('rating__rating')).anotate(num_of_ratings=Count('rating'))

        # In a context dict. store all the details about movie in a list
        context_dictionary = {
            "details": [movie_obj.name, movie_obj.release_date, movie_obj.actors, movie_obj.producer,
                        movie_obj.trailer, movie_obj.genre, movie_obj.description, movie_obj.avg_rating,
                        movie_obj.num_of_ratings]
        }

    # If movie object does not exist, set movie details to None
    except Movie.DoesNotExist:
        context_dictionary["details"] = None

    return context_dictionary

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
    this_years_favorite = Movie.object.filter(release_date__gte=str(datetime.year) + '-01-01'). \
        annotate(avg_rating=Avg('rating__rating')).order_by('-avg_rating')[0]

    context_dictionary = {
        "top_movies": top_movies,
        "recently_added": recently_added,
        "this_years_favorite": this_years_favorite,
    }

    return render(request, "index.html", context_dictionary)


def about(request):
    return render(request, 'about.html')


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

    return render(request, 'register.html', context={'user_form': user_form,
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
        return render(request, 'login.html')


@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)
    # Take the user back to the homepage.
    return redirect(reverse('rotten_potatoes:index'))


def movie(request, movie_name_slug):
    context_dictionary = get_movie_context(movie_name_slug)

    # Render movie page with context dict. information passed
    return render(request, "movie.html", context_dictionary)


@login_required
def edit_movie(request, movie_name_slug):
    form = EditMovieForm()
    initial_dict = {}

    # Get movie from the database, if not present return HttpResponse
    if not check_movie_exists(movie_name_slug):
        return HttpResponse("Movie " + movie_name_slug + " does not exist.")

    movie_obj = Movie.object.get(slug=movie_name_slug)

    # Check if user is not the movie producer and admin
    if request.user.pk != movie_obj.user.pk and not request.user.is_superuser():
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
        initial_dict["cover"] = movie_obj.cover

        # Get from with initial values set to pre-existing movie data
        form = EditMovieForm(initial=initial_dict)
        # Get context dict. with movie and form info
        context_dict = get_movie_context(movie_name_slug)
        context_dict["form"] = form
        return render(request, "edit.html", context_dict)

    if request.method == "POST":
        form = EditMovieForm(request.POST)

        if form.is_valid():
            form = EditMovieForm(request.POST, instance=movie_obj)
            form.save()
            context_dictionary = get_movie_context(movie_name_slug)

            return render(request, "movie.html", context_dictionary)

        else:
            print(form.errors)
            return HttpResponse(form.errors)


@login_required
def add_comment(request, movie_name_slug):
    # Check if movie exists
    if not check_movie_exists(movie_name_slug):
        return HttpResponse("Movie " + movie_name_slug + " does not exist")

    form = AddCommentForm()

    if request.method == "POST":
        form = AddCommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.movie = Movie.object.get(slug=movie_name_slug)
            comment.time_posted = now()
            comment.save()

            return movie(request, movie_name_slug)
        else:
            print(form.errors)

    return render(request, "addcomment.html", {"form": form})


@login_required
def rate_movie(request, movie_name_slug):
    # Check if movie exists
    if not check_movie_exists(movie_name_slug):
        return HttpResponse("Movie " + movie_name_slug + " does not exist.")

    form = AddRatingForm()
    if request.method == "POST":
        form = AddRatingForm(request.POST)
        if form.is_valid():
            rating_obj = form.save(commit=False)
            rating_obj.user = request.user
            rating_obj.movie = Movie.object.get(slug=movie_name_slug)
            rating_obj.rating = int(form.rating)
            rating_obj.save()

            return redirect("/rotten_potatoes/")
        else:
            print(form.errors)
            return HttpResponse(form.errors)
    else:
        context_dict = get_movie_context(movie_name_slug)
        context_dict['form'] = form

        return render(request, "ratemovie.html", context_dict)


@login_required
def add_movie(request):
    form = MovieForm()

    if request.method == "POST":
        if not request.user.producer:
            return redirect('/rotten_potatoes/')

        form = MovieForm(request.POST)

        if form.is_valid():
            movie_form = form.save(commit=False)
            # Set producer and datetime before saving to database
            movie_form.user = request.user
            movie_form.upload_date = now()
            movie_form.save()

            return redirect('/rotten_potatoes/')
        else:
            print(form.errors)

    return render(request, 'addmovie.html', {"form": form})


@login_required
def account(request):
    context_dict = {}
    try:
        profile = UserProfile.object.get(user=request.user)
        context_dict = get_user_context(profile)

    except UserProfile.DoesNotExist:
        context_dict["user_details"] = None

    return render(request, "account.html", context_dict)


@login_required
def edit_account(request):
    form = EditAccountForm()

    if request.method == "POST":
        form = EditAccountForm(request.POST)
        if form.is_valid():
            # Retrieve pk of user
            profile = UserProfile.object.get(user=request.user)
            # Associate change with user object in database
            form = EditAccountForm(request.POST, instance=profile)
            # Save form
            form.save()

            redirect('/rotten_potatoes/')
        else:
            return HttpResponse(form.errors)

    else:
        initial_dict = {}
        form = EditAccountForm()

        profile = UserProfile.object.get(user=request.user)
        initial_dict["profile_pic"] = profile.profile_pic
        initial_dict["description"] = profile.description
        form = EditAccountForm(initial=initial_dict)

        context_dict = get_user_context(profile)
        context_dict["form"] = form
        return render(request, 'edit.html', context_dict)


# Ratings view with default sorting by movie rating
def ratings(request):
    form = RatingsPageForm(request.POST or None)

    if form.is_valid():
        movies = Movie.object.annotate(avg_rating=Avg("rating__rating")).annotate(num_of_ratings=Count("rating"))
        # get this years favorite
        this_years_favorite = Movie.object.filter(release_date__gte=str(datetime.year) + '-01-01'). \
            annotate(avg_rating=Avg('rating__rating')).order_by('-avg_rating')[0]

        clean_data = form.cleaned_data()
        sort_by = clean_data.get('sort_by')
        genre = clean_data.get('genre')

        if genre is not None:
            sorted_list = movies.filter(genre=genre).order_by(sort_by)
        else:
            sorted_list = movies.order_by(sort_by)

        context_dict = {
            "form": form,
            "movie_list": sorted_list,
            "this_years_favorite": this_years_favorite,
        }

        return render(request, "ratings.html", context_dict)

    else:
        print(form.errors)
        return HttpResponse(form.errors)


def get_movie_context(movie_name_slug):
    context_dictionary = {}
    try:
        # Get movie object to get details
        movie_obj = Movie.object.get(slug=movie_name_slug)
        # Get average rating and number of ratings
        movie_obj = movie_obj.annotate(avg_rating=Avg('rating__rating')).anotate(num_of_ratings=Count('rating'))

        # In a context dict. store all the details about movie in a list
        context_dictionary = {
            "movie": movie_obj
        }

    # If movie object does not exist, set movie details to None
    except Movie.DoesNotExist:
        context_dictionary["movie"] = None

    return context_dictionary


def get_user_context(profile):
    context_dict = {"profile": profile}

    # Check if user is a producer
    if profile.producer:
        # Get all movies added by this user
        context_dict["added_movies"] = Movie.object.filter(producer=profile.user)
    else:
        context_dict["added_movies"] = None
        # Get all rating made by this user, then get associated movie name
        context_dict["rated_movies"] = Rating.object.filter(user=profile.user)

    return context_dict


def check_movie_exists(movie_name_slug):
    # Check if movie exists
    try:
        Movie.object.get(slug=movie_name_slug)
        return True
    except Movie.DoesNotExist:
        return False

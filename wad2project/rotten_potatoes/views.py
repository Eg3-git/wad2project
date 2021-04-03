from django.contrib import messages
from django.db.models import Count, Avg
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from rotten_potatoes.forms import *
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from datetime import datetime, timedelta
from django.utils.timezone import now


def index(request):
    # Query the top 5 movies
    top_movies = Movie.objects.annotate(avg_rating=Avg('rating__rating')).order_by('-avg_rating')[:5]

    # Get movies which were uploaded in past 14 days
    recently_added = Movie.objects.filter(upload_date__gte=datetime.now() - timedelta(days=14))

    # Change this weeks favorite to this years favorite #
    current_year = datetime.now().date().strftime("%Y")  # Get current year
    try:
        this_years_favorite = Movie.objects.annotate(avg_rating=Avg('rating__rating'))
        this_years_favorite = this_years_favorite.filter(release_date__range=
                                                         [current_year + '-01-01',
                                                          current_year + '-12-31']).order_by('-avg_rating')[0]
    except:
        this_years_favorite = None

    context_dictionary = {
        "top_movies": top_movies,
        "recently_added": recently_added,
        "this_years_favorite": this_years_favorite,
    }

    # Check if user is producer or not
    try:
        profile = UserProfile.objects.get(user=request.user)
        context_dictionary['is_producer'] = profile.producer
    except:
        context_dictionary['is_producer'] = False

    return render(request, "rotten_potatoes/index.html", context_dictionary)


def about(request):
    return render(request, 'rotten_potatoes/about.html')


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
            # Check if user is producer or not
            if request.POST['producer'] == "Yes":
                profile.producer = True
            else:
                profile.producer = False

            if 'profile_pic' in request.FILES:
                profile.profile_pic = request.FILES['profile_pic']

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
                messages.error(request, "Your Rotten Potatoes account is disabled")
                return redirect(reverse("rotten_potatoes:login"))
        else:
            # Bad login details were provided. So we can't log the user in.
            print(f"Invalid login details: {username}, {password}")
            messages.error(request, "Invalid login details")
            return redirect(reverse("rotten_potatoes:login"))
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
    # Get movie from the database, if not present return HttpResponse
    if not check_movie_exists(movie_name_slug):
        messages.error(request, "Sorry, movie you tried to access does not exists")
        return redirect("/rotten_potatoes/")

    context_dictionary = get_movie_context(movie_name_slug)

    try:
        context_dictionary["comments"] = Comment.objects.filter(movie=Movie.objects.get(slug=movie_name_slug))
    except:
        context_dictionary["comments"] = None

    # Render movie page with context dict. information passed
    return render(request, "rotten_potatoes/movie.html", context_dictionary)


@login_required
def edit_movie(request, movie_name_slug):
    form = EditMovieForm()
    initial_dict = {}

    # Get movie from the database, if not present return HttpResponse
    if not check_movie_exists(movie_name_slug):
        messages.error(request, "Sorry, movie you tried to access does not exists")
        return redirect("/rotten_potatoes/")

    movie_obj = Movie.objects.get(slug=movie_name_slug)

    # Check if user is not the movie producer and admin
    if UserProfile.objects.get(user=request.user) != movie_obj.producer and not request.user.is_superuser:
        messages.error(request, "You are not allowed to edit this movie")
        return redirect("/rotten_potatoes/")

    if request.method == "GET":
        # Fill initial dictionary with pre-existing values
        initial_dict["name"] = movie_obj.name
        initial_dict["release_date"] = movie_obj.release_date
        initial_dict["actors"] = movie_obj.actors
        initial_dict["trailer"] = movie_obj.trailer
        initial_dict["genre"] = movie_obj.genre
        initial_dict["description"] = movie_obj.description
        initial_dict["cover"] = movie_obj.cover

        # Get from with initial values set to pre-existing movie data
        form = EditMovieForm(initial=initial_dict)
        # Get context dict. with movie and form info
        context_dict = get_movie_context(movie_name_slug)
        context_dict["form"] = form
        context_dict["movie"] = movie_name_slug
        return render(request, "rotten_potatoes/edit.html", context_dict)

    if request.method == "POST":
        form = EditMovieForm(request.POST, request.FILES)

        if form.is_valid():
            form = EditMovieForm(request.POST, instance=movie_obj)
            form.save()

            return redirect(reverse("rotten_potatoes:movie", kwargs={"movie_name_slug": movie_name_slug}))

        else:
            print(form.errors)
            return HttpResponse(form.errors)


@login_required
def add_comment(request, movie_name_slug):
    # Check if movie exists
    if not check_movie_exists(movie_name_slug):
        messages.error(request, "Sorry, movie you tried to access does not exists")
        return redirect("/rotten_potatoes/")

    form = AddCommentForm()

    if request.method == "POST":
        form = AddCommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = UserProfile.objects.get(user=request.user)
            comment.movie = Movie.objects.get(slug=movie_name_slug)
            comment.time_posted = now()
            comment.save()

            return redirect(reverse('rotten_potatoes:movie', kwargs={"movie_name_slug": movie_name_slug}))
        else:
            print(form.errors)

    return render(request, "rotten_potatoes/addcomment.html", context={"form": form,
                                                                       "movie": Movie.objects.get(
                                                                           slug=movie_name_slug)})


@login_required
def delete_comment(request, movie_name_slug, comment_pk):
    # Check if user is associated with the comment
    user = UserProfile.objects.get(user=request.user)
    comment = Comment.objects.get(pk=comment_pk)
    if user != comment.user:
        messages.error(request, "You can not delete this comment")
        return redirect(reverse("rotten_potatoes:movie", kwargs={"movie_name_slug": movie_name_slug}))

    comment.delete()
    messages.success(request, "You have successfully deleted your comment")
    return redirect(reverse("rotten_potatoes:movie", kwargs={"movie_name_slug": movie_name_slug}))


@login_required
def rate_movie(request, movie_name_slug):
    # Check if movie exists
    if not check_movie_exists(movie_name_slug):
        messages.error(request, "Sorry, movie you tried to access does not exists")
        return redirect("/rotten_potatoes/")

    # Check if user is not producer of the movie (producers cant rate their own movie)
    if UserProfile.objects.get(user=request.user).pk == Movie.objects.get(slug=movie_name_slug).producer.pk:
        messages.error(request, "You can not rate your own movie")
        return redirect(reverse("rotten_potatoes:movie", kwargs={"movie_name_slug": movie_name_slug}))

    form = AddRatingForm()
    if request.method == "POST":
        form = AddRatingForm(request.POST)
        if form.is_valid():
            rating_obj = form.save(commit=False)
            rating_obj.user = UserProfile.objects.get(user=request.user)
            rating_obj.movie = Movie.objects.get(slug=movie_name_slug)
            rating_obj.save()

            return redirect(reverse('rotten_potatoes:movie',
                                    kwargs={'movie_name_slug': movie_name_slug}))
        else:
            print(form.errors)
            return HttpResponse(form.errors)
    else:
        context_dict = get_movie_context(movie_name_slug)
        context_dict['form'] = form

        return render(request, "rotten_potatoes/ratemovie.html", context_dict)


@login_required
def add_movie(request):
    if not UserProfile.objects.get(user=request.user).producer:
        messages.error(request, "Sorry, you can not add a movie")
        return redirect("/rotten_potatoes/")

    form = MovieForm()

    if request.method == "POST":
        form = MovieForm(request.POST)

        if form.is_valid():
            movie_form = form.save(commit=False)
            # Set producer and datetime before saving to database
            movie_form.producer = UserProfile.objects.get(user=request.user)
            movie_form.upload_date = now()

            if 'cover' in request.FILES:
                movie_form.cover = request.FILES['cover']

            movie_form.save()

            return redirect(reverse('rotten_potatoes:movie', kwargs={"movie_name_slug": movie_form.slug}))
        else:
            print(form.errors)

    return render(request, 'rotten_potatoes/addmovie.html', {"form": form})


@login_required
def delete_movie(request, movie_name_slug):

    # Get movie from the database, if not present return HttpResponse
    if not check_movie_exists(movie_name_slug):
        messages.error(request, "Sorry, movie you tried to access does not exists")
        return redirect("/rotten_potatoes/")
    movie_obj = Movie.objects.get(slug=movie_name_slug)

    # Check user is the producer of the movie or superuser
    if UserProfile.objects.get(user=request.user) != movie_obj.producer and not request.user.is_superuser:
        messages.error(request, "You are not permitted to delete this movie")
        return redirect(reverse('rotten_potatoes:movie', kwargs={"movie_name_slug": movie_name_slug}))

    movie_obj.delete()

    messages.success(request, "You have successfully deleted the movie.")
    return redirect("/rotten_potatoes/")


@login_required
def account(request):
    context_dict = {}
    try:
        profile = UserProfile.objects.get(user=request.user)
        context_dict = get_user_context(profile)
        try:
            movies = Movie.objects.filter(producer=UserProfile.objects.get(user=request.user))
            context_dict['movies'] = movies
        except:
            context_dict['movies'] = None

    except:
        context_dict["profile"] = None

    return render(request, "rotten_potatoes/account.html", context_dict)


@login_required
def edit_account(request):
    form = EditAccountForm()

    if request.method == "POST":
        form = EditAccountForm(request.POST, request.FILES)
        if form.is_valid():
            # Retrieve pk of user
            profile = UserProfile.objects.get(user=request.user)
            # Associate change with user object in database
            form = EditAccountForm(request.POST, instance=profile)
            # Save form
            form.save()

            return redirect(reverse("rotten_potatoes:account"))
        else:
            return HttpResponse(form.errors)

    else:
        initial_dict = {}
        form = EditAccountForm()

        profile = UserProfile.objects.get(user=request.user)
        initial_dict["profile_pic"] = profile.profile_pic
        initial_dict["description"] = profile.description
        form = EditAccountForm(initial=initial_dict)

        context_dict = get_user_context(profile)
        context_dict["form"] = form
        return render(request, 'rotten_potatoes/editaccount.html', context_dict)


# Ratings view with default sorting by movie rating
def ratings(request):
    form = RatingsPageForm(request.POST or None)

    if form.is_valid():
        try:
            movies = Movie.objects.annotate(avg_rating=Avg("rating__rating")).annotate(num_of_ratings=Count("rating"))

            current_year = datetime.now().date().strftime("%Y")  # Get current year
            # get this years favorite
            this_years_favorite = Movie.objects.filter(release_date__gte=current_year + '-01-01'). \
                annotate(avg_rating=Avg('rating__rating')).order_by('-avg_rating')[0]

            clean_data = form.cleaned_data()
            sort_by = clean_data.get('sort_by')
            genre = clean_data.get('genre')

            if genre is not None:
                movie_list = movies.filter(genre=genre).order_by(sort_by)
            else:
                movie_list = movies.order_by(sort_by)

            context_dict = {
                "form": form,
                "movie_list": movie_list,
                "this_years_favorite": this_years_favorite,
            }

        except:
            context_dict = {
                "form": form,
                "movie_list": None,
                "this_years_favorite": None,
            }

        return render(request, "rotten_potatoes/ratings.html", context_dict)

    else:
        print(form.errors)
        return HttpResponse(form.errors)


def get_movie_context(movie_name_slug):
    context_dictionary = {}
    try:
        # Get movie object to get details
        movie_obj = Movie.objects.annotate(avg_rating=Avg('rating__rating')).annotate(num_of_ratings=Count('rating'))
        # Get average rating and number of ratings
        movie_obj = movie_obj.get(slug=movie_name_slug)

        context_dictionary = {
            "movie": movie_obj,
        }

        # Convert url into embedded video link
        try:
            url = movie_obj.trailer
            x = url.split("=")
            newLink = "https://www.youtube.com/embed/" + x[-1]

            context_dictionary['urlLink'] = newLink

        # Convert url into embedded video link
        except:
            newLink = "https://www.youtube.com/embed/dQw4w9WgXcQ"
            context_dictionary['urlLink'] = newLink

    # If movie object does not exist, set movie details to None
    except:
        context_dictionary["movie"] = None

    return context_dictionary


def get_user_context(profile):
    context_dict = {"profile": profile}

    # Check if user is a producer
    if profile.producer:
        # Get all movies added by this user
        context_dict["added_movies"] = Movie.objects.filter(producer=profile)
    else:
        context_dict["added_movies"] = None
        # Get all rating made by this user, then get associated movie name
        context_dict["rated_movies"] = Rating.objects.filter(user=profile)

    return context_dict


def check_movie_exists(movie_name_slug):
    # Check if movie exists
    try:
        Movie.objects.get(slug=movie_name_slug)
        return True
    except:
        return False


2

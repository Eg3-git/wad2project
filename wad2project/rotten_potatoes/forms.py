from django import forms
from django.contrib.auth.models import User
from .models import *


# List of genres to pick from
genres = [
    ("action", "Action"),
    ("comedy", "Comedy"),
    ("drama", "Drama"),
    ("fantasy", "Fantasy"),
    ("horror", "Horror"),
    ("mystery", "Mystery"),
    ("romance", "Romance"),
    ("thriller", "Thriller"),
    ("sci-fi", "Sci-Fi"),
    ("western", "Western"),
    ("experimental", "Experimental")
]

sort_by_list = [
    ("-avg_rating", "Rating Descending"),
    ("avg_rating", "Rating Ascending"),
    ("-name", "Name <A-Z>"),
    ("name", "Name <Z-A>"),
    ("-num_of_ratings", "Number Of Ratings"),
]

ratings = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')]


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    producer = forms.BooleanField(label="Are you a producer")

    class Meta:
        model = User
        fields = ('username', 'password')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('profile_pic', 'description',)


class MovieForm(forms.ModelForm):
    name = forms.CharField(max_length=128, help_text="Please, enter the name of the movie.", required=True)
    release_date = forms.DateField(help_text="Please, select the release date.", widget=forms.SelectDateWidget(years=range(1900, 2100)), required=False)
    actors = forms.CharField(max_length=256, help_text="Please, enter list of actors.", required=False)
    trailer = forms.URLField(max_length=128, help_text="Please, enter the trailer link.", required=False)
    genre = forms.ChoiceField(label="Genre", choices=genres, help_text="Please, select movie genre.")
    description = forms.CharField(max_length=1024, widget=forms.Textarea, required=False)
    slug = forms.SlugField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Movie
        exclude = ('producer', 'upload_date', )


class EditMovieForm(forms.ModelForm):
    name = forms.CharField(max_length=128, help_text="Please, enter the name of the movie.", required=True)
    release_date = forms.DateField(help_text="Please, select the release date.", initial="Unknown", required=False)
    actors = forms.CharField(max_length=256, help_text="Please, enter list of actors.", required=False)
    trailer = forms.URLField(max_length=128, help_text="Please, enter the trailer link.", required=False)
    genre = forms.ChoiceField(label="Genre", widget=forms.CheckboxInput, choices=genres, help_text="Please, select movie genre.")
    description = forms.CharField(max_length=1024, widget=forms.Textarea, required=False)

    class Meta:
        model = Movie
        exclude = ('producer', 'upload_date', 'slug', )


class RatingsPageForm(forms.Form):
    genre = forms.ChoiceField(label="Genres", widget=forms.CheckboxInput, choices=genres, initial=None)
    sort_by = forms.ChoiceField(label="Sort by", widget=forms.CheckboxInput, choices=sort_by_list, initial="-rating")


class AddRatingForm(forms.ModelForm):
    rating = forms.ChoiceField(widget=forms.RadioSelect, choices=ratings)

    class Meta:
        model = Rating
        exclude = ('user', 'movie')


class AddCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class EditAccountForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('profile_pic', 'description')

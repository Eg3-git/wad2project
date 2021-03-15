from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from rotten_potatoes.models import*
from rotten_potatoes.forms import*
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from datetime import datetime


def index(request):
    pass


def about(request):
    return render(request, "rotten_potatoes/about.html")


def register(request):
    pass


def user_login(request):
    pass


@login_required
def user_logout(request):
    pass


def movie(request):
    pass


@login_required
def edit_movie(request):
    pass


@login_required
def add_comment(request):
    pass


@login_required
def rate_movie(request):
    pass


@login_required
def add_movie(request):
    pass


@login_required
def account(request):
    pass


@login_required
def edit_account(request):
    pass


def ratings(request):
    pass

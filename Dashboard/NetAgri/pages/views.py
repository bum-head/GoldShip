from django.shortcuts import render

from .regions import places_for_frontend


def home(request):
    return render(request, "pages/home.html", {"ner": places_for_frontend()})


def about(request):
    return render(request, "pages/about.html")

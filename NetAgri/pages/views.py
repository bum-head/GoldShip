from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from .regions import places_for_frontend

from . import climate_service as cs


def home(request):
    return render(request, "pages/home.html")

def about(request):
    return render(request, "pages/about.html")

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("marketplace:crop_list")
    else:
        form = UserCreationForm()

    return render(
        request,
        "pages/register.html",
        {"form": form},
    )

def dashboard(request):
    return render(request, "pages/dashboard.html", {"ner": places_for_frontend()})

@require_GET
@never_cache
def climate_weather(request):
    try:
        loc = cs.parse_coords(request.GET)
        return JsonResponse(cs.fetch_raw_weather(**loc))
    except cs.ApiError as e:
        return JsonResponse({"error": e.message}, status=e.status)


@require_GET
@never_cache
def climate_rating(request):
    try:
        loc = cs.parse_coords(request.GET)
        weather = cs.normalize_weather(cs.fetch_raw_weather(**loc))
        return JsonResponse({"location": loc, "weather": weather,
                             "rating": cs.rate_weather(weather)})
    except cs.ApiError as e:
        return JsonResponse({"error": e.message}, status=e.status)

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render



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

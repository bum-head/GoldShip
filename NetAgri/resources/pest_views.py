from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone

from marketplace.models import Region

from .forms import PestReportForm
from .models import PestReport
from .views import _selected


def pests(request):
    rid = _selected(request)
    reviewed = PestReport.objects.filter(status="reviewed").select_related("region")
    if rid:
        reviewed = reviewed.filter(region_id=rid)

    since = timezone.localdate() - timedelta(days=30)
    counts = (
        reviewed.filter(observed_on__gte=since)
        .values("crop_name", "region__name")
        .annotate(n=Count("id"))
        .order_by("-n", "crop_name")[:10]
    )
    mine = []
    if request.user.is_authenticated:
        mine = PestReport.objects.filter(reporter=request.user).select_related("region")

    return render(request, "resources/pests.html", {
        "reports": reviewed[:30], "counts": counts, "mine": mine,
        "regions": Region.objects.all(), "selected": rid,
    })


@login_required
def report_pest(request):
    if request.method == "POST":
        form = PestReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.save()
            return redirect("resources:pests")
    else:
        form = PestReportForm()
    return render(request, "resources/pest_form.html", {"form": form})

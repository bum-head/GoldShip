from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from marketplace.models import Region

from .advisor import AdvisorError, ask, build_context, local_summary


@login_required
def advisor(request):
    answer = error = None
    form = {"region": "", "crop": "", "question": ""}
    if request.method == "POST":
        form = {k: request.POST.get(k, "").strip() for k in form}
        form["question"] = form["question"][:500]
        region = Region.objects.filter(pk=form["region"]).first() if form["region"].isdigit() else None
        if not region or not form["question"]:
            error = "Choose a region and type a question."
        else:
            try:
                answer = ask(form["question"], build_context(region, form["crop"]))
            except AdvisorError:
                answer = local_summary(region, form["crop"])
                error = "AI answers are switched off, so here is a climate and price summary instead."
    return render(request, "resources/advisor.html", {
        "regions": Region.objects.all(), "form": form, "answer": answer, "error": error,
    })

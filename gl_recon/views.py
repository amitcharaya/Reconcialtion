from django.shortcuts import render, redirect
from .forms import GLAccountForm


def create_gl(request):
    next_url = request.GET.get("next")

    if request.method == "POST":
        form = GLAccountForm(request.POST)
        if form.is_valid():
            gl = form.save()

            return redirect(f"/gl/opening/?gl_id={gl.id}&next={next_url}")

    else:
        form = GLAccountForm()

    return render(request, "gl_recon/create_gl.html", {"form": form})

from .forms import GLOpeningBalanceForm
from .models import GLAccount


def set_opening_balance(request):
    gl_id = request.GET.get("gl_id")
    next_url = request.GET.get("next")

    gl = GLAccount.objects.get(id=gl_id)

    if request.method == "POST":
        form = GLOpeningBalanceForm(request.POST)
        if form.is_valid():
            opening = form.save(commit=False)
            opening.gl_account = gl
            opening.save()

            # ✅ Redirect back to original page
            return redirect(next_url or "/")

    else:
        form = GLOpeningBalanceForm()

    return render(request, "gl_recon/opening_balance.html", {
        "form": form,
        "gl": gl
    })
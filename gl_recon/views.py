from .services.gl_reconciliation_services import run_gl_reconciliation


def dashboard(request):
    from datetime import date

    data = run_gl_reconciliation(date.today())

    return render(request, "dashboard.html", {
        "gl_data": data
    })

from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse




def gl_reconciliation_view(request):
    """
    HTML Dashboard View
    URL: /gl-reconciliation/
    """

    date_str = request.GET.get("date")

    if date_str:
        settlement_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        from datetime import date
        settlement_date = date.today()

    data = run_gl_reconciliation(settlement_date)

    return render(request, "dashboard.html", {
        "gl_data": data
    })


def gl_reconciliation_api(request):
    """
    API View (for AJAX / future React dashboard)
    URL: /api/gl-reconciliation/
    """

    date_str = request.GET.get("date")

    if not date_str:
        return JsonResponse({"error": "date parameter required"}, status=400)

    settlement_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    data = run_gl_reconciliation(settlement_date)

    return JsonResponse(data, safe=False)
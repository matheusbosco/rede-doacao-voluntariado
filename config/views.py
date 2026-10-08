from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


# Métodos recusados retornam 405 mesmo sem token CSRF.
@require_GET
@csrf_exempt
def health(request):
    """Confirma que a aplicação responde, sem consultar o banco."""
    return JsonResponse({"status": "ok"})

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from recipes.models import Recipe


def redirect_short_link(request, encoded_id):
    """Перенаправить короткую ссылку на страницу рецепта."""
    try:
        decoded_id = force_str(urlsafe_base64_decode(encoded_id))
        recipe_id = int(decoded_id)
        get_object_or_404(Recipe, id=recipe_id)
        return HttpResponseRedirect(f'/recipes/{recipe_id}/')
    except (ValueError, TypeError):
        return HttpResponse(status=404)

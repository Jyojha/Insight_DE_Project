from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
import neo4j_utils

@require_http_methods("GET")
def find_path(request):

    params = request.GET

    try:
        from_cnn = int(params['from_cnn'])
        to_cnn = int(params['to_cnn'])

    except (KeyError, ValueError):
        return HttpResponseBadRequest("bad request")

    path = neo4j_utils.find_path(from_cnn, to_cnn)

    if path is None:
        return JsonResponse({"result": 'not_found'})

    return JsonResponse({"result": 'success', "path": path})



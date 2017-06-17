from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page
import neo4j_utils

@require_http_methods("GET")
def index(request):
    return render_to_response('index.html')

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


@require_http_methods("GET")
def matching_streets(request):
    params = request.GET
    search_term = params.get('term', '')

    return JsonResponse({"candidates": neo4j_utils.find_matching_streets(search_term)})


@require_http_methods("GET")
def intersecting_streets(request):
    params = request.GET

    try:
        street = params['street']
    except KeyError:
        return HttpResponseBadRequest("street not passed")

    return JsonResponse({"streets": neo4j_utils.find_street_intersections(street)})




import json
from datetime import timezone as dt_timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse,HttpResponseRedirect,HttpResponse
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator

from .models import ShortenedURL, Click
from .utils import generate_unique_code

# Create your views here.
url_validator=URLValidator(schemes=['http', 'https'])

@csrf_exempt
def create_url(request):
    if request.method!='POST':
        return JsonResponse({'error':'Only POST requests are allowed'}, status=405)
    try:
        data=json.loads(request.body)
    except ValueError:
        return JsonResponse({'error':'Request body must be valid JSON'}, status=400)
    
    if not isinstance(data, dict):
        return JsonResponse({'error':'Request body must be a JSON object'}, status=400)

    url=data.get('url')
    if not isinstance(url, str) or not url.strip():
        return JsonResponse({'error':'URL is required and must be a non-empty string'}, status=400)
    url=url.strip()

    try:
        url_validator(url)
    except ValidationError:
        return JsonResponse({'error':'URL must be a valid http or https URL'}, status=400)
    
    expires_at=None
    expires_raw=data.get('expiresAt')
    if expires_raw is not None:
        try:
            expires_at=parse_datetime(expires_raw)
        except (TypeError, ValueError):
            expires_at=None
        
        if expires_at is None:
            return JsonResponse({'error':'expiresAt must be a valid date-time string'}, status=400)
        if timezone.is_naive(expires_at):
            expires_at=timezone.make_aware(expires_at, timezone=dt_timezone.utc)
        if expires_at<=timezone.now():
            return JsonResponse({'error':'expiresAt must be a future date-time'}, status=400)

    link=ShortenedURL.objects.create(
        code=generate_unique_code(),
        url=url,
        expiration_date=expires_at
    )
    shortened_url=f"{settings.BASE_URL.rstrip('/')}/{link.code}"
    return JsonResponse({'code':link.code,'shortURL':shortened_url,'url':link.url,'expires_at':link.expiration_date.isoformat() if link.expiration_date else None}, status=201)

def redirect_to_url(request, code):
    try:
        link=ShortenedURL.objects.get(code=code)
    except ShortenedURL.DoesNotExist:
        return JsonResponse({'error':'Shortened URL not found'}, status=404)
    if link.expiration_date is not None and link.expiration_date<=timezone.now():
        return JsonResponse({'error':'Shortened URL has expired'}, status=410)
    Click.objects.create(
        shorter_url=link,
        client_info=request.META.get('HTTP_USER_AGENT', ''),
        referring_url=request.META.get('HTTP_REFERER', '')
    )
    return HttpResponseRedirect(link.url)

def url_stats(request,code):
    try:
        link=ShortenedURL.objects.get(code=code)
    except ShortenedURL.DoesNotExist:
        return JsonResponse({'error':'Shortened URL not found'}, status=404)
    clicks=link.clicks.all()
    total_clicks=clicks.count()
    last_click=clicks.order_by('-clicked_at').first()
    clicks_by_day=(clicks.values('clicked_at__date').annotate(count=Count('id')).order_by('clicked_at__date'))
    clicks_by_day_data=[{"date":item['clicked_at__date'], "count":item['count']} for item in clicks_by_day]
    return JsonResponse({
        "code":link.code,
        "url":link.url,
        "created_at":link.created_at.isoformat(),
        "lastClickedAt":(last_click.clicked_at.isoformat() if last_click else None),
        "clicksByDay":clicks_by_day_data,
    })

def list_urls(request):
    if request.method!='GET':
        return JsonResponse({'error':'Only GET requests are allowed'}, status=405)
    page=request.GET.get('page',1)
    limit=request.GET.get('limit',20)
    try:
        page=int(page)
        limit=int(limit)
    except ValueError:
        return JsonResponse({'error':'page and limit must be integers'}, status=400)
    
    if page<1:
        return JsonResponse({'error':'page must be a greater than 0'}, status=400)
    if limit<1:
        return JsonResponse({'error':'limit must be a greater than 0'}, status=400)
    urls=ShortenedURL.objects.all().order_by('-created_at')
    paginator=Paginator(urls, limit)
    current_page=paginator.get_page(page)
    results=[]
    for link in current_page:
        results.append({
            "code":link.code,
            "shortened_url":request.build_absolute_uri(f'/{link.code}/'),
            "url":link.url,
            "created_at":link.created_at.isoformat(),
            "expires_at":link.expiration_date.isoformat() if link.expiration_date else None
        })
    return JsonResponse({
        "page":current_page.number,
        "limit":limit,
        "total":paginator.count,
        "total_pages":paginator.num_pages,
        "results":results
    })

@csrf_exempt
def delete_url(request, code):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Only DELETE requests are allowed'}, status=405)
    try:
        link=ShortenedURL.objects.get(code=code)
    except ShortenedURL.DoesNotExist:
        return JsonResponse({'error':'Shortened URL not found'}, status=404)
    link.delete()
    return HttpResponse(status=204)


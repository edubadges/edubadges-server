import urllib
import urlparse

from mainsite.models import BadgrApp


def set_url_query_params(url, **kwargs):
    """
    Given a url, possibly including query parameters, return a url with the given query parameters set, replaced on a
    per-key basis.
    """
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(kwargs)
    url_parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(url_parts)


def get_session_badgr_app(request):
    try:
        return BadgrApp.objects.get(pk=request.session.get('badgr_app_pk', None))
    except BadgrApp.DoesNotExist:
        return None


def set_session_badgr_app(request, badgr_app):
    request.session['badgr_app_pk'] = badgr_app.pk
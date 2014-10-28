import jingo
import urllib
import datetime


@jingo.register.function
def obfuscate_email(value):
  l = len(value)
  obfu = "'%s','%s','%s'" % (value[:l/3], value[l/3:l/3*2], value[l/3*2:])
  return "<script>document.write('<a href=\"mailto:',%s,'\">',%s,'</a>')</script>" % (obfu, obfu)


@jingo.register.function
def get_full_path_escaped(request):
    #full_path = ('http', ('', 's')[request.is_secure()], '://', request.META['HTTP_HOST'], request.path)
    full_path = ('http', ('', 's')[request.is_secure()], '://', 'concentricsky.com', request.path)
    return urllib.quote(''.join(full_path), '')


@jingo.register.filter
def short_date_format(value):
    return value.strftime('%B %d, %Y')


@jingo.register.filter
def long_date_format(value):
    return value.strftime('%B %d, %Y %H:%M')


@jingo.register.function
def divisible_by(value, num):
    """Check if a variable is divisible by a number."""
    return value % num == 0    
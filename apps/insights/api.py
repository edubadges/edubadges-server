from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from insights.permissions import TeachPermission
from issuer.models import BadgeInstance


class InsightsView(APIView):
    permission_classes = (TeachPermission,)

    def post(self, request, **kwargs):
        lang = request.data.get('lang', 'en')

        current_date = timezone.now().date()
        year = request.data.get('year', current_date.year)
        start_of_year = current_date.replace(year=year, month=1, day=1)
        end_of_year = current_date.replace(year=year, month=12, day=31)

        institution = request.user.institution
        name_lang = 'name_english' if lang == 'en' else 'name_dutch'
        assertions = BadgeInstance.objects \
            .filter(issuer__faculty__institution=institution) \
            .filter(created_at__gte=start_of_year) \
            .filter(created_at__lt=end_of_year) \
            .annotate(week=TruncWeek('created_at')).values('week') \
            .annotate(nbr=Count('id')) \
            .annotate(award_type_count=Count('award_type', distinct=True)) \
            .values('week', 'nbr', 'badgeclass_id', 'badgeclass__name', 'award_type', 'issuer_id',
                    f"issuer__{name_lang}",
                    'issuer__faculty_id', f"issuer__faculty__{name_lang}") \
            .all()

        return Response(list(assertions), status=status.HTTP_200_OK)

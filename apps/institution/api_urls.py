from django.conf.urls import url

from institution.api import FacultyList

urlpatterns = [
    url(r'^faculties$', FacultyList.as_view(), name='api_faculty_list')
    ]


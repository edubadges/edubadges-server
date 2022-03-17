import badgrlog

from entity.api import BaseEntityListView, BaseEntityDetailView

from lti13.models import LtiCourse
from lti13.serializers import LtiCourseSerializer
from mainsite.permissions import TeachPermission

logger = badgrlog.BadgrLogger()


class LtiCourseDetail(BaseEntityDetailView):
    model = LtiCourse
    permission_classes = (TeachPermission,)
    serializer_class = LtiCourseSerializer
    http_method_names = ['delete']


class LtiCourseDetailList(BaseEntityListView):
    model = LtiCourse
    permission_classes = (TeachPermission,)
    serializer_class = LtiCourseSerializer
    http_method_names = ['post']

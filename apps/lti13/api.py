import badgrlog

from entity.api import BaseEntityListView, BaseEntityDetailView
from insights.permissions import TeachPermission
from lti13.models import LtiCourse
from lti13.serializers import LtiCourseSerializer

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

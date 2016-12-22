import logging
import pkg_resources

from django.template import Template, Context
from HTMLParser import HTMLParser
from xblock.core import XBlock
from xblock.fields import Scope, Boolean, Dict, List, String
from xblock.fragment import Fragment
from xblockutils.studio_editable import StudioEditableXBlockMixin

from student.models import anonymous_id_for_user, User


_ = lambda text: text
log = logging.getLogger(__name__)
html_parser = HTMLParser()


class EdxAdaptXBlock(StudioEditableXBlockMixin, XBlock):
    """
    This XBlock automatically registers students in the EdxAdapt instance
    using parameters configured by the teaching staff: params, skills, edx_adapt_api_url
    """

    has_author_view = True

    display_name = String(
        default='Adaptive Learning Enrollment',
        scope=Scope.content,
    )

    params = Dict(
        default={'pg': 0.25, 'ps': 0.25, 'pi': 0.1, 'pt': 0.5, 'threshold': 0.99},
        display_name=_('BKT params'),
        help=_('Parameters for Bayesian Knowledge Tracing (BKT) model'),
        scope=Scope.content
    )

    skills = List(
        default=[
            'center', 'shape', 'spread', 'x axis', 'y axis', 'h to d',
            'd to h', 'histogram', 'None'
        ],
        display_name=_('Course skills list'),
        scope=Scope.content,
        help=_(
            'List of skills of this course. Each problem addresses certain skill. '
            'Special skill "None" is used for those problems which belong to none.'
        )
    )
    edx_adapt_api_url = String(
        default='',
        display_name=_('Edx Adapt API base URL'),
        scope=Scope.content,
        help=_('Edx Adapt API base URL, e.g. https://edx-adapt.example.com:443/api/v1')
    )

    student_is_registered = Boolean(
        default=False,
        scope=Scope.preferences
    )

    fail_registration_msg = String(
        default=_(
            "There was a technical issue while we were configuring your adaptive learning session. Please try to "
            "refresh this page or contact technical staff if problem persists."
        ),
        display_name=_("Assistance message if enrollment fails"),
        help=_("Assistance message with steps student can do to improve Edx Adapt enrollment, e.g. email could be "
               "added for asking for technical support."),
        scope=Scope.content,
    )

    editable_fields = ('params', 'skills', 'edx_adapt_api_url', 'fail_registration_msg')

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def ugettext(self, text):
        """
        For backward compatibility with older version of XBlock module released before Mar 22, 2016

        See https://github.com/edx/XBlock/blame/ab636a82bc23c3f65a618e438637d518b209790f/xblock/core.py#L204
        """
        return text

    def get_anonymous_student_id(self):
        """
        Returns course non-specific anonymous student id compatible with
        anonymous id used by Capa Problems.
        """

        return anonymous_id_for_user(
            User.objects.get(
                id=self.runtime.user_id), None
        )

    def get_course_id(self):
        """
        Returns short course id compatible with course ids used by
        Open edX <=> edx adapt communication javascript.
        """
        return self.course_id.course

    def student_view(self, context=None):
        """
        Configures user in edx-adapt if it wasn't configured before
        """
        html = self.resource_string("static/html/student_view.html")
        anonymous_student_id = self.get_anonymous_student_id()
        frag = Fragment(html.format(
            self=self,
            anonymous_student_id=anonymous_student_id,
            student_is_registered=self.student_is_registered,
            course_id=self.get_course_id(),
            edx_adapt_api_url=self.edx_adapt_api_url.rstrip('/'),
            params=self.params,
            skills=self.skills,
            fail_registration_msg=self.fail_registration_msg,
        ))
        frag.add_css(self.resource_string("static/css/edxadapt.css"))
        frag.add_javascript(self.resource_string('static/js/src/edxadapt.js'))
        frag.initialize_js('EdxAdaptXBlock')

        return frag

    def author_view(self, context=None):
        """
        Separate view for Open edX Studio.
        It displays current xblock settings instead of trying
        to register user in the EdxAdapt
        """
        html = self.resource_string('static/html/author_view.html').format(
            edx_adapt_api_url=self.edx_adapt_api_url,
            params=self.params,
            skills=self.skills,
            fail_registration_msg=self.fail_registration_msg,
        )
        frag = Fragment(html)
        return frag

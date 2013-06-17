# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from sadiki.core.models import Requestion
from sadiki.core.workflow import IMMEDIATELY_PERMANENT_DECISION, \
    PERMANENT_DECISION, DECISION, \
    TEMP_PASS_TRANSFER, TEMP_DISTRIBUTION_TRANSFER, IMMEDIATELY_DECISION, \
    DECISION_DISTRIBUTION, PASS_DISTRIBUTED, \
    DISTRIBUTED_ARCHIVE, STATUS_CHANGE_TRANSITIONS
from sadiki.logger.models import Logger

DECISION_TRANSFERS = (DECISION, IMMEDIATELY_DECISION, PERMANENT_DECISION,
                     IMMEDIATELY_PERMANENT_DECISION, TEMP_DISTRIBUTION_TRANSFER,
                     TEMP_PASS_TRANSFER)
TEMP_DECISION_TRANSFERS = (TEMP_DISTRIBUTION_TRANSFER, TEMP_PASS_TRANSFER)
DISTRIBUTION_TRANSFERS = (DECISION_DISTRIBUTION, PASS_DISTRIBUTED,)
DISMISS_TRANSFERS = (DISTRIBUTED_ARCHIVE,)


class RequestionLogs(TemplateView):
    u"""
    Отображение публичных логов изменений заявки
    """
    template_name = "logger/requestion_logs.html"

    def get(self, request, requestion_id):
        requestion = get_object_or_404(Requestion, id=requestion_id)
        logs = Logger.objects.filter(content_type=ContentType.objects.get_for_model(Requestion),
            object_id=requestion.id).order_by('datetime')
        logs_with_messages = []
        for log in logs:
            messages = log.loggermessage_set.filter_for_user(request.user)
            if log.action_flag in STATUS_CHANGE_TRANSITIONS or messages:
                logs_with_messages.append([log, messages])
        if request.user.is_authenticated():
            if request.user.is_operator():
                self.template_name = "logger/requestion_logs_for_operator.html"
            elif request.user.is_requester():
                self.template_name = "logger/requestion_logs_for_account.html"
        return self.render_to_response({'logs_with_messages': logs_with_messages, 'requestion': requestion})

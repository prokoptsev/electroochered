# -*- coding: utf-8 -*-
import datetime
from django.contrib import messages
from django.contrib.auth import get_backends, login
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm, PasswordResetForm
from django.contrib.auth.views import password_change
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from sadiki.authorisation.forms import EmailResetForm
from sadiki.authorisation.models import VerificationKey
from sadiki.core.utils import get_user_by_email
from sadiki.core.workflow import EMAIL_VERIFICATION
from sadiki.logger.models import Logger


class EmailVerification(TemplateView):
    u"""Изменение заявки пользователем"""
    template_name = 'authorisation/email_verification.html'

    def get(self, request, key):
        verification_key_object = get_object_or_404(VerificationKey, key=key)
        if not verification_key_object.is_valid:
            message = u'Ссылка недействительна, попробуйте получить новую.'
            return self.render_to_response({'message': message})
        user = verification_key_object.user
        if get_user_by_email(user.email):
            message = u'Адрес, который вы пытаетесь подтвердить уже зарегистрирован и подтвержден.'
            return self.render_to_response({'message': message})
        else:
            verification_key_object.unused = False
            verification_key_object.save()
            profile = user.get_profile()
            profile.email_verified = True
            profile.save()
            message = u'Адрес электронной почты %s подтвержден!' % user.email
            messages.info(request, message)

            action_flag = EMAIL_VERIFICATION
            context_dict = {'email': user.email}
            extra = {
                'user': user,
                'obj': profile,
            }
            Logger.objects.create_for_action(action_flag,
                                             context_dict=context_dict,
                                             extra=extra)

            if user.is_active:
                backend = get_backends()[1]
                user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
                login(request, user)

            return HttpResponseRedirect(reverse('frontpage'))

class ResetPasswordRequest(TemplateView):
    template_name = 'authorisation/reset_password_request.html'

    def get(self, request):
        form = EmailResetForm()
        return self.render_to_response({'form': form})

    def post(self, request):
        form = EmailResetForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.info(request, u'''
                 На указанный в профиле адрес электронной почты(%s)
                 выслано письмо с инструкцией по восстановлению пароля.
            ''' % user.email)
            return HttpResponseRedirect(reverse('frontpage'))
        return self.render_to_response({'form': form})


class ResetPassword(TemplateView):
    template_name = 'authorisation/reset_password.html'

    def dispatch(self, request, key):
        verification_key_object = get_object_or_404(VerificationKey, key=key)
        if not verification_key_object.is_valid:
            return {'message': u'Данная ссылка уже использовалась, попробуйте получить новую.'}
        return TemplateView.dispatch(self, request,
            verification_key_object=verification_key_object)

    def get(self, request, verification_key_object):
        form = SetPasswordForm(verification_key_object.user)
        return self.render_to_response({'form': form,
            'username':verification_key_object.user.email})

    def post(self, request, verification_key_object):
        user = verification_key_object.user
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            verification_key_object.valid = False
            verification_key_object.save()
            if user.is_active:
                backend = get_backends()[1]
                user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
                login(request, user)
            messages.info(request,
                u"Пароль пользователя успешно изменён." % user)
            return HttpResponseRedirect(reverse('frontpage'))
        return self.render_to_response({'form': form, 'username': user.email})


def password_set(request):
    u"""
    Если у пользователя не задан пароль, то не нужно запрашивать его
    """
    if request.user.password and request.user.has_usable_password():
        raise Http404
    return password_change(request, template_name=u'authorisation/passwd_set.html',
                           password_change_form=SetPasswordForm)


def is_allowed_send_confirm(user):
    u"""
    Проверяем, соответствие пользователя условиям для отправки письма
    со ссылкой для подтверждения почтового ящика:
    - авторизирован
    - в профиле указан email
    - email еще не подтвержден
    - не запрашивал подтверждения последние 5 минут (от спама)
    """
    if user.is_anonymous():
        raise PermissionDenied
    if any((not user.email, user.get_profile().email_verified)):
        return False
    try:
        last_key = VerificationKey.objects.filter(user=user).latest('created')
    except ObjectDoesNotExist:
        last_key = None
    if last_key:
        t_delta = (datetime.datetime.now() - last_key.created).seconds
        return t_delta > 300
    else:
        return True


def send_confirm_letter(request):
    u""""
    Если пользователь проходит проверку - отправляем письмо с кодом подтверждения
    """
    if is_allowed_send_confirm(request.user):
        user = request.user
        key = VerificationKey.objects.create_key(user)
        # print key.key
        key.send_email_verification()
        return HttpResponse('ok')
    return HttpResponse('not allowed')

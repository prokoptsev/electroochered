# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings
import datetime


def birth_date_validator(value):
    current_date = datetime.date.today()
    end_date = current_date.replace(
            year=current_date.year - settings.MAX_CHILD_AGE)
    if value < end_date:
        raise ValidationError(u"Возраст ребёнка превышает максимальный")
    elif value > current_date:
        raise ValidationError(u"Дата рождения не может превышать текущую дату")


def registration_date_validator(value):
    current_date = datetime.date.today()
    if value.date() > current_date:
        raise ValidationError(u"Дата регистрации не может превышать текущую дату")


snils_validator = RegexValidator(
    '^[0-9]{3}-[0-9]{3}-[0-9]{3} [0-9]{2}$',
    message=u'СНИЛС должен быть записан в формате xxx-xxx-xxx xx'
)

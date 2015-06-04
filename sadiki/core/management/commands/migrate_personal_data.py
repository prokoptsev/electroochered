# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from sadiki.core.models import Profile, Requestion
from sadiki.core.workflow import CHANGE_USER_PERSONAL_DATA
from sadiki.core.workflow import CHANGE_CHILD_PERSONAL_DATA
from sadiki.logger.models import Logger
from personal_data.models import ChildPersData, UserPersData


class Command(BaseCommand):
    help_text = '''Usage: manage.py migrate_personal_data'''

    def handle(self, *args, **options):
        all_users = User.objects.select_related().all()
        for user in all_users:
            new_data = {}
            if hasattr(user, 'profile'):
                profile = user.profile
                if hasattr(profile, 'pdata'):
                    pdata = profile.pdata
                    if not user.first_name and not user.last_name:
                        user.first_name = pdata.first_name
                        user.last_name = pdata.last_name
                        new_data['first_name'] = pdata.first_name
                        new_data['last_name'] = pdata.last_name
                        profile.middle_name = pdata.second_name
                        new_data['middle_name'] = pdata.second_name
                    profile.town = pdata.settlement
                    new_data['town'] = pdata.settlement
                    profile.street = pdata.street
                    new_data['street'] = pdata.street
                    profile.house = pdata.house
                    new_data['house'] = pdata.house
                    profile.mobile_number = pdata.phone
                    new_data['phone'] = pdata.phone
                if (not user.first_name and not user.last_name
                                and profile.first_name):
                    user.first_name = profile.first_name
                    new_data['first_name'] = profile.first_name
                profile.save()
            user.save()
            if new_data:
                Logger.objects.create_for_action(
                    CHANGE_USER_PERSONAL_DATA,
                    context_dict={'new_data': new_data},
                    extra={'user': user},
                    reason=u'Обновление до v1.9'
                )

        all_child_personal_data = ChildPersData.objects.all()
        for pdata in all_child_personal_data:
            new_data = {}
            requestion = pdata.application
            requestion.child_middle_name = pdata.second_name
            new_data['child_middle_name'] = pdata.second_name
            requestion.child_last_name = pdata.last_name
            new_data['child_last_name'] = pdata.last_name
            if not requestion.name:
                requestion.name = pdata.first_name
                new_data['child_first_name'] = pdata.first_name
            requestion.save()
            Logger.objects.create_for_action(
                CHANGE_CHILD_PERSONAL_DATA,
                context_dict={'new_data': new_data},
                extra={'user': requestion.profile.user},
                reason=u'Обновление до v1.9'
            )



'''
        print u'Переносим Ф.И.О. заявителей'
        pdatas = UserPersData.objects.all()
        for pdata in pdatas:
            profile = pdata.profile
            user = profile.user
            if not user.first_name and pdata.first_name:
                user.first_name = pdata.first_name
                user.last_name = pdata.last_name
                user.save()
                profile.middle_name = pdata.second_name
                profile.save()
        profiles = Profile.objects.all()
        for profile in profiles:
            user = profile.user
            if not user.first_name and profile.first_name:
                user.first_name = profile.first_name
                user.save()

        print u'Переносим прочие данные заявителей'
        pdatas = UserPersData.objects.all()
        for pdata in pdatas:
            profile = pdata.profile
            profile.town = pdata.settlement
            profile.street = pdata.street
            profile.house = pdata.house
            profile.mobile_number = pdata.phone
            profile.save()

        print u'Переносим данные заявок'
        reqdatas = ChildPersData.objects.all()
        for reqdata in reqdatas:
            requestion = reqdata.application
            requestion.child_middle_name = reqdata.second_name
            requestion.child_last_name = reqdata.last_name
            if not requestion.name:
                requestion.name = reqdata.first_name
            requestion.save()
'''

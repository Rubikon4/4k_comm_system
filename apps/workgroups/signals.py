from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import WorkGroupMembership


@receiver(post_save, sender=WorkGroupMembership)
def on_workgroup_membership_change(sender, instance, **kwargs):
    """
    При добавлении или изменении членства в группе синхронизирует
    состав workgroup-чата этой группы.
    """
    from apps.chats.services import sync_workgroup_chat_members
    sync_workgroup_chat_members(instance.workgroup)

from django.dispatch import receiver
from room_types.models import RoomType
from django.db.models.signals import pre_delete


@receiver(pre_delete, sender=RoomType)
def change_room_room_type(*, instance, **_):  # todo need test
    """Change room's room_type to default before delete."""
    default_room_type = RoomType.objects.filter(office_id=instance.office_id, title='Рабочее место').first()
    instance.rooms.update(room_type=default_room_type)

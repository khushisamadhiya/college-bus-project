from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Seat
from .views import send_seat_allotment_email  # Import email function

@receiver(post_save, sender=Seat)
def send_seat_allotment_email_signal(sender, instance, created, **kwargs):
    if created and instance.student:  # Jab seat assign ho tab email bhejo
        send_seat_allotment_email(instance.student)

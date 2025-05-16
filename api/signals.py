# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Bus, Seat

@receiver(post_save, sender=Bus)
def create_seats_for_bus(sender, instance, created, **kwargs):
    if created:
        # Remove existing seats (if any)
        Seat.objects.filter(bus=instance).delete()

        seats = []
        seat_number = 1
        if instance.has_sleeper:
            for row in range(1, instance.total_rows + 1):
                # Lower berth
                seats.append(Seat(
                    bus=instance,
                    seat_number=seat_number,
                    seat_type='LOWER',
                    row=row,
                    column='L'
                ))
                seat_number += 1
                # Upper berth
                seats.append(Seat(
                    bus=instance,
                    seat_number=seat_number,
                    seat_type='UPPER',
                    row=row,
                    column='U'
                ))
                seat_number += 1
        else:
            for row in range(1, instance.total_rows + 1):
                for col in ['A', 'B', 'C']:
                    seats.append(Seat(
                        bus=instance,
                        seat_number=seat_number,
                        seat_type='SEATER',
                        row=row,
                        column=col
                    ))
                    seat_number += 1

        Seat.objects.bulk_create(seats)

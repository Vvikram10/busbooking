from django.db import models
from django.contrib.auth.models import User

class Bus(models.Model):
    bus_number = models.CharField(max_length=20)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    
    # Bus configuration
    total_rows = models.IntegerField(default=10)  # Number of rows
    has_sleeper = models.BooleanField(default=True)
    
    # Base fares
    seater_fare = models.DecimalField(max_digits=10, decimal_places=2)
    lower_berth_fare = models.DecimalField(max_digits=10, decimal_places=2)
    upper_berth_fare = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.bus_number}: {self.source} to {self.destination}"
    
    def get_total_seats(self):
        if self.has_sleeper:
            return self.total_rows * 2
        else:
            return self.total_rows * 3  # Assuming 3 seats per row for non-sleeper

class Seat(models.Model):
    SEAT_TYPE_CHOICES = (
        ('SEATER', 'Seater'),
        ('LOWER', 'Lower Berth'),
        ('UPPER', 'Upper Berth'),
    )
    
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.IntegerField()
    seat_type = models.CharField(max_length=10, choices=SEAT_TYPE_CHOICES)
    row = models.IntegerField()
    column = models.CharField(max_length=2)  # A, B, C or L (lower), U (upper)
    
    class Meta:
        unique_together = ('bus', 'seat_number')
    
    def get_fare(self):
        if self.seat_type == 'SEATER':
            return self.bus.seater_fare
        elif self.seat_type == 'LOWER':
            return self.bus.lower_berth_fare
        else:  # UPPER
            return self.bus.upper_berth_fare
    
    def __str__(self):
        return f"{self.seat_type} {self.seat_number} on Bus {self.bus.bus_number}"

class Booking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_fare = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Booking {self.id} by {self.user.username}"

class BookedSeat(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booked_seats')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('booking', 'seat')
    
    def __str__(self):
        return f"{self.seat.seat_type} {self.seat.seat_number} for {self.booking}"
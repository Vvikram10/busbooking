from django.contrib import admin
from .models import Bus, Seat, Booking, BookedSeat

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('bus_number', 'source', 'destination', 'departure_time', 'arrival_time', 'has_sleeper')
    search_fields = ('bus_number', 'source', 'destination')
    list_filter = ('has_sleeper', 'departure_time')

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('seat_number', 'bus', 'seat_type', 'row', 'column')
    list_filter = ('seat_type', 'bus')
    search_fields = ('seat_number',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bus', 'booking_date', 'status', 'total_fare')
    list_filter = ('status', 'booking_date')
    search_fields = ('user__username', 'bus__bus_number')

@admin.register(BookedSeat)
class BookedSeatAdmin(admin.ModelAdmin):
    list_display = ('booking', 'seat')
    search_fields = ('booking__id', 'seat__seat_number')

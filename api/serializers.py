from rest_framework import serializers
from .models import Bus, Seat, Booking, BookedSeat
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class SeatSerializer(serializers.ModelSerializer):
    is_booked = serializers.SerializerMethodField()
    fare = serializers.DecimalField(max_digits=10, decimal_places=2, source='get_fare')
    
    class Meta:
        model = Seat
        fields = ['id', 'seat_number', 'seat_type', 'row', 'column', 'is_booked', 'fare']
    
    def get_is_booked(self, obj):
        return BookedSeat.objects.filter(
            seat=obj, 
            booking__status='CONFIRMED'
        ).exists()

class BusSerializer(serializers.ModelSerializer):
    available_seats_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Bus
        fields = ['id', 'bus_number', 'source', 'destination', 'departure_time', 
                 'arrival_time', 'total_rows', 'has_sleeper', 'seater_fare', 
                 'lower_berth_fare', 'upper_berth_fare', 'available_seats_count']
    
    def get_available_seats_count(self, obj):
        booked_seats = BookedSeat.objects.filter(
            seat__bus=obj, 
            booking__status='CONFIRMED'
        ).count()
        return obj.get_total_seats() - booked_seats

class BookedSeatSerializer(serializers.ModelSerializer):
    seat_number = serializers.IntegerField(source='seat.seat_number')
    seat_type = serializers.CharField(source='seat.seat_type')
    
    class Meta:
        model = BookedSeat
        fields = ['id', 'seat_number', 'seat_type']

class BookingSerializer(serializers.ModelSerializer):
    booked_seats = BookedSeatSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    seat_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    
    class Meta:
        model = Booking
        fields = ['id', 'user', 'bus', 'booking_date', 'status', 'total_fare', 'booked_seats', 'seat_ids']
        read_only_fields = ['id', 'booking_date', 'total_fare']
    
    def create(self, validated_data):
        seat_ids = validated_data.pop('seat_ids')
        bus = validated_data.get('bus')
        user = self.context['request'].user
        
        # Calculate total fare based on selected seats
        total_fare = Decimal(0)
        for seat_id in seat_ids:
            try:
                seat = Seat.objects.get(id=seat_id, bus=bus)
                total_fare += seat.get_fare()
            except Seat.DoesNotExist:
                raise serializers.ValidationError(f"Seat ID {seat_id} not found")
        
        # Create booking with transaction to ensure atomicity
        with transaction.atomic():
            # Check if any seats are already booked
            for seat_id in seat_ids:
                if BookedSeat.objects.filter(
                    seat_id=seat_id, 
                    booking__status='CONFIRMED'
                ).exists():
                    raise serializers.ValidationError(
                        f"Seat {Seat.objects.get(id=seat_id).seat_number} is already booked"
                    )
            
            # Create booking
            booking = Booking.objects.create(
                user=user,
                bus=bus,
                status='CONFIRMED',
                total_fare=total_fare
            )
            
            # Create booked seats
            for seat_id in seat_ids:
                BookedSeat.objects.create(booking=booking, seat_id=seat_id)
        
        return booking
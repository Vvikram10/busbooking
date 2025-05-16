from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db import transaction
from .models import Bus, Seat, Booking, BookedSeat
from .serializers import BusSerializer, SeatSerializer, BookingSerializer, UserSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
    user = request.user  # Currently logged-in user
    serializer = UserSerializer(user, many=False)  # Serialize user object
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_all_buses(request):
    buses = Bus.objects.all()
    serializer = BusSerializer(buses, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_bus_details(request, bus_id):
    try:
        bus = Bus.objects.get(id=bus_id)
        serializer = BusSerializer(bus)
        return Response(serializer.data)
    except Bus.DoesNotExist:
        return Response({"error": "Bus not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_bus_seats(request, bus_id):
    try:
        seats = Seat.objects.filter(bus_id=bus_id)
        serializer = SeatSerializer(seats, many=True)
        return Response(serializer.data)
    except:
        return Response({"error": "Error fetching seats"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_seats(request):
    serializer = BookingSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            # Create booking
            booking = serializer.save()
            
            # Send real-time update via WebSocket
            bus_id = booking.bus.id
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"bus_{bus_id}",
                {
                    "type": "seat_update",
                    "bus_id": bus_id,
                }
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if booking.status == 'CANCELLED':
        return Response({"error": "Booking is already cancelled"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Cancel booking
    with transaction.atomic():
        booking.status = 'CANCELLED'
        booking.save()
        
        # Send real-time update via WebSocket
        bus_id = booking.bus.id
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"bus_{bus_id}",
            {
                "type": "seat_update",
                "bus_id": bus_id,
            }
        )
    
    return Response({"message": "Booking cancelled successfully"}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user)
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def initialize_bus_seats(request):
#     """Admin function to initialize seats for a bus"""
#     bus_id = request.data.get('bus_id')
#     try:
#         bus = Bus.objects.get(id=bus_id)
        
#         # Delete existing seats
#         Seat.objects.filter(bus=bus).delete()
        
#         # Create new seats based on bus configuration
#         seats = []
#         seat_number = 1
        
#         if bus.has_sleeper:
#             # Create sleeper configuration (lower + upper berths)
#             for row in range(1, bus.total_rows + 1):
#                 # Lower berth
#                 seats.append(Seat(
#                     bus=bus,
#                     seat_number=seat_number,
#                     seat_type='LOWER',
#                     row=row,
#                     column='L'
#                 ))
#                 seat_number += 1
                
#                 # Upper berth
#                 seats.append(Seat(
#                     bus=bus,
#                     seat_number=seat_number,
#                     seat_type='UPPER',
#                     row=row,
#                     column='U'
#                 ))
#                 seat_number += 1
#         else:
#             # Create seater configuration (3 seats per row)
#             for row in range(1, bus.total_rows + 1):
#                 for col in ['A', 'B', 'C']:
#                     seats.append(Seat(
#                         bus=bus,
#                         seat_number=seat_number,
#                         seat_type='SEATER',
#                         row=row,
#                         column=col
#                     ))
#                     seat_number += 1
        
#         # Bulk create the seats
#         Seat.objects.bulk_create(seats)
        
#         return Response({"message": f"Created {len(seats)} seats for bus {bus.bus_number}"}, 
#                         status=status.HTTP_201_CREATED)
        
#     except Bus.DoesNotExist:
#         return Response({"error": "Bus not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
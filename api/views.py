
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db import transaction
from .models import Bus, Seat, Booking, BookedSeat
from .serializers import BusSerializer, RegisterSerializer, SeatSerializer, BookingSerializer, UserSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # ⬇️ Iss line se JWT token generate hota hai
        refresh = RefreshToken.for_user(user)

        user_serializer = UserSerializer(user)
        return Response({
            'user': user_serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'detail': 'Both username and password are required'}, status=400)
    
    user = authenticate(username=username,password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        user_serializer = UserSerializer(user)
        return Response({
            'user': user_serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    return Response({'detail': 'Invalid credentials'}, status=401)

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


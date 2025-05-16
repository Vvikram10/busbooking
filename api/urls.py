from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    
    path('get_user/', views.get_user, name='get_user'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('buses/', views.get_all_buses, name='all-buses'),
    path('buses/<int:bus_id>/', views.get_bus_details, name='bus-details'),
    path('buses/<int:bus_id>/seats/', views.get_bus_seats, name='bus-seats'),
    path('bookings/', views.book_seats, name='book-seats'),
    path('bookings/cancel/<int:booking_id>/', views.cancel_booking, name='cancel-booking'),
    path('my-bookings/', views.my_bookings, name='my-bookings'),
]
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import Seat
from .serializers import SeatSerializer

class BusSeatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.bus_id = self.scope['url_route']['kwargs']['bus_id']
        self.group_name = f"bus_{self.bus_id}"
        
        # Join bus group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial seat status
        await self.send_seat_status()
    
    async def disconnect(self, close_code):
        # Leave bus group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    @database_sync_to_async
    def get_seat_status(self):
        seats = Seat.objects.filter(bus_id=self.bus_id)
        serializer = SeatSerializer(seats, many=True)
        return serializer.data
    
    async def send_seat_status(self):
        seats = await self.get_seat_status()
        await self.send(text_data=json.dumps({
            'type': 'seat_status',
            'seats': seats
        }))
    
    async def seat_update(self, event):
        # Send updated seat status
        await self.send_seat_status()
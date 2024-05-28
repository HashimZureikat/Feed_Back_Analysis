# feedback/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class FeedbackConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "feedback_group",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "feedback_group",
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        await self.channel_layer.group_send(
            "feedback_group",
            {
                'type': 'feedback_message',
                'message': message
            }
        )

    async def feedback_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))

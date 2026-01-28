from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^pvp/match/(?P<match_id>\d+)/$', consumers.PvpMatchConsumer.as_asgi()),
    re_path(r'^pvp/queue/$', consumers.PvpQueueConsumer.as_asgi()),
]
from django.urls import re_path
from . import ws_consumers 


websocket_urlpatterns = [
    re_path(r'^pvp/match/(?P<match_id>\d+)/$', ws_consumers.PvpMatchConsumer.as_asgi()),
    re_path(r'^pvp/queue/$', ws_consumers.PvpQueueConsumer.as_asgi()),
]
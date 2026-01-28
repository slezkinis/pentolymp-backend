# pvp/middleware.py
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from users.models import User

@database_sync_to_async
def get_user(token_key):
    try:
        access_token = AccessToken(token_key)
        user_id = access_token['user_id']
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Получаем токен из query string
        query_string = scope.get('query_string', b'').decode()
        print(query_string)
        query_params = parse_qs(query_string)
        
        token = query_params.get('token', [None])[0]
        print(token)
        
        if token:
            scope['user'] = await get_user(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
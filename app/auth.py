import json
import jwt
from functools import wraps
from flask import request, jsonify
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, ImmatureSignatureError
from . import cache, config



def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        #проверяем кэш:
        cache_data = cache.get(token)
        if cache_data:
            cache_data = json.loads(cache_data)
            allowed_methods = cache_data.get('methods')  #доступные методы
            id_firm = cache_data.get('id_firm')

            if allowed_methods is None:
                return jsonify({'message': 'Cache data is incomplete!'}), 403
        else:
            try:
                decoded = jwt.decode(token, config['SECRET_KEY'], algorithms='HS256')
                allowed_methods = decoded['methods']
                id_firm = decoded['id']

                # Кэшируем разрешенные методы на 1 час
                cache.set(token, json.dumps({'methods': allowed_methods, 'id_firm': id_firm}), ex=3600)
            except ExpiredSignatureError:
                return jsonify({'message':'token has expired'}), 401
            except ImmatureSignatureError:
                return jsonify({'message': 'token has not start yet'}), 401
            except InvalidTokenError:
                return jsonify({'message': 'invalid token'}), 401

        #проверяем разрешенные методы
        method_name = request.endpoint.split('.')[-1]  #сюда попадает название функции, например, def calculate_risk()

        if method_name not in allowed_methods:
            return jsonify({'message': 'Method not allowed!'}), 403

        # Добавляем id_firm в kwargs, чтобы его можно было использовать в функции
        kwargs['id_firm'] = id_firm

        return f(*args, **kwargs)
    return decorator

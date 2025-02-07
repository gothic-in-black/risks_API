import json
import jwt
from functools import wraps
from flask import request, jsonify
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, ImmatureSignatureError
from . import cache, config


def token_required(f):
    """
    Decorator for checking the existence and validity of the JWT token.
    It sends the id_firm in function in case of successful check.
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        # Get token from headers
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        # Checking cache for token info
        cache_data = cache.get(token)
        if cache_data:
            cache_data = json.loads(cache_data)
            # Get allowed methods and id_firm from cache
            allowed_methods = cache_data.get('methods')
            id_firm = cache_data.get('id_firm')

            # If token doesn't contain methods
            if allowed_methods is None:
                return jsonify({'message': 'Token data is incomplete. Please contact support to check available methods.'}), 403
        else:
            try:
                # Decode token using the secret key
                decoded = jwt.decode(token, config['SECRET_KEY'], algorithms='HS256')
                # Get allowed methods and id_firm from decoded token
                allowed_methods = decoded['methods']
                id_firm = decoded['id']

                # Save token info in cache for 1 hour
                cache.set(token, json.dumps({'methods': allowed_methods, 'id_firm': id_firm}), ex=3600)
            except ExpiredSignatureError:
                return jsonify({'message':'Token has expired'}), 401
            except ImmatureSignatureError:
                return jsonify({'message': 'Token has not start yet'}), 401
            except InvalidTokenError:
                return jsonify({'message': 'Invalid token'}), 401

        # Get method name from the endpoint
        method_name = request.endpoint.split('.')[-1]

        # Check if the current method is available
        if method_name not in allowed_methods:
            return jsonify({'message': 'Method not allowed!'}), 403

        # Pass the id_firm to the function
        kwargs['id_firm'] = id_firm

        # Call the original function with arguments
        return f(*args, **kwargs)
    return decorator

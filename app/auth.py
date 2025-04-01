import json
import logging
import jwt
from functools import wraps
from flask import request, jsonify
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, ImmatureSignatureError
from . import cache, config


# Create a logger instance
logger = logging.getLogger(__name__)

def token_required(f):
    """
    Decorator for checking the existence and validity of the JWT token.
    It sends the id_firm and type_risk in function in case of successful check.
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        # Get token from headers
        token = request.headers.get('Authorization')
        if not token:
            logger.warning("Request without token from IP: %s", request.remote_addr)
            return jsonify({'message': 'Token is missing!'}), 401

        # Checking cache for token info
        cache_data = cache.get(token)
        if cache_data:
            cache_data = json.loads(cache_data)
            # Get allowed methods and id_firm from cache
            allowed_methods = cache_data.get('methods')
            id_firm = cache_data.get('id_firm')
            type_risk = cache_data.get('type_risk')

            # If token doesn't contain methods
            if allowed_methods is None:
                logger.warning('Token without access rights: %s', id_firm)
                return jsonify({'message': 'Token data is incomplete. Please contact support to check available methods.'}), 403
            logger.info("Get token from cache. IP: %s, ID firm: %s", request.remote_addr, id_firm)
        else:
            try:
                # Decode token using the secret key
                decoded = jwt.decode(token, config['SECRET_KEY'], algorithms='HS256')
                # Get allowed methods and id_firm from decoded token
                allowed_methods = decoded['methods']
                id_firm = decoded['id']
                type_risk = decoded['type_risk']

                # Save token info in cache for 1 hour
                cache.set(token, json.dumps({'methods': allowed_methods, 'id_firm': id_firm, 'type_risk': type_risk}), ex=3600)
                logger.info("The token has been successfully decrypted and added to the cache. ID firm: %s", id_firm)
            except ExpiredSignatureError:
                logger.warning("Expired token from IP: %s", request.remote_addr)
                return jsonify({'message':'Token has expired'}), 401
            except ImmatureSignatureError:
                logger.warning("Token has not start yet. IP: %s", request.remote_addr)
                return jsonify({'message': 'Token has not start yet'}), 401
            except InvalidTokenError:
                logger.warning("Invalid token from IP: %s", request.remote_addr)
                return jsonify({'message': 'Invalid token'}), 401

        # Get method name from the endpoint
        method_name = request.endpoint.split('.')[-1]

        # Check if the current method is available
        if method_name not in allowed_methods:
            logger.warning("Access to the method '%s' forbidden for ID firm: %s", method_name, id_firm)
            return jsonify({'message': 'Method not allowed!'}), 403

        # Pass the id_firm and risk_type to the function
        kwargs['id_firm'] = id_firm
        kwargs['type_risk'] = type_risk

        logger.info("Access to the method '%s' is allowed. ID firm: %s", method_name, id_firm)

        # Call the original function with arguments
        return f(*args, **kwargs)
    return decorator

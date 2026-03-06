from flask import Blueprint, request, jsonify
from app.services import UserService
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

user_bp = Blueprint('user', __name__, url_prefix='/api/users')


@user_bp.route('/init-admin', methods=['POST'])
def create_system_admin():
    """Create system admin user (initial setup).

    Returns: User object with admin credentials
    """
    try:
        data = request.get_json() or {}
        username = data.get('username', 'admin')
        password = data.get('password', 'admin')

        user = UserService.create_system_admin(
            username=username, password=password)
        return jsonify({
            'message': 'System admin created successfully',
            'user': user.to_dict()
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    user = UserService.get_user_by_username(username)
    if not user or not UserService.verify_password(user, password):
        return jsonify({'error': 'Invalid username or password'}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token, 'user': user.to_dict()}), 200


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = UserService.get_user_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

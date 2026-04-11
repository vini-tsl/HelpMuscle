"""
TimbuMuscle - Blueprint Admin
Rotas de debug protegidas por variável de ambiente (não expostas em produção).
"""
import os
from flask import Blueprint, jsonify, request
from models import Usuario
from db import db
from sqlalchemy import text

admin_bp = Blueprint('admin', __name__)


def _admin_authorized():
    """Autorização simples: só funciona se DEBUG=True + admin secret válido."""
    secret = request.args.get('admin_secret', '')
    expected = os.environ.get('ADMIN_SECRET', '')
    return os.environ.get('FLASK_ENV') == 'development' and secret == expected and expected


@admin_bp.route('/debug/users')
def debug_users():
    if not _admin_authorized():
        return jsonify({'error': 'Não autorizado'}), 403

    usuarios = Usuario.query.all()
    debug_info = [{
        'id': u.id,
        'nome': u.nome,
        'email': u.email,
        'key': u.key,
        'tipo': u.tipo,
        'ultimo_acesso': u.ultimo_acesso.isoformat() if u.ultimo_acesso else 'Nunca',
    } for u in usuarios]

    return jsonify({'total_usuarios': len(debug_info), 'usuarios': debug_info})


@admin_bp.route('/debug/routes')
def debug_routes():
    if not _admin_authorized():
        return jsonify({'error': 'Não autorizado'}), 403

    from flask import current_app
    routes = [{
        'endpoint': rule.endpoint,
        'methods': list(rule.methods),
        'path': str(rule),
    } for rule in current_app.url_map.iter_rules()]

    return jsonify(routes)

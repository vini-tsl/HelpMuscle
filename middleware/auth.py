"""
TimbuMuscle - Middleware de autenticação
Garante que todas as rotas protegidas verifiquem a sessão do usuário.
"""
from functools import wraps
from datetime import datetime
from flask import session, redirect, url_for, flash
from models import Usuario
from db import db
from werkzeug.wrappers import Response


def login_required(f):
    """
    Decorator que exige autenticação por sessão.
    Injeta o objeto `usuario` como primeiro argumento da função decorada.
    A rota deve receber `key` como argumento (vindo da URL).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_key = session.get('user_key')
        if not user_key:
            flash('Faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))

        usuario = Usuario.query.filter_by(key=user_key).first()
        if not usuario:
            session.pop('user_key', None)
            flash('Sessão expirada. Faça login novamente.', 'warning')
            return redirect(url_for('auth.login'))

        route_key = kwargs.get('key')
        if route_key and route_key != usuario.key:
            flash('Acesso não autorizado.', 'danger')
            return redirect(url_for('auth.login'))

        # Atualizar flag online e ultimo acesso durante o uso
        usuario.ultimo_acesso = datetime.utcnow()
        usuario.online = True
        db.session.commit()

        # Passa o usuário como argumento extra
        return f(usuario, *args, **kwargs)
    return decorated_function


def profissional_required(f):
    """Decorator que exige que o usuário seja do tipo profissional."""
    @wraps(f)
    def decorated_function(usuario, *args, **kwargs):
        if usuario.tipo != 'profissional':
            flash('Acesso restrito a profissionais.', 'danger')
            return redirect(url_for('usuarios.usuarios', key=usuario.key))
        return f(usuario, *args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator que exige que o usuário seja admin."""
    @wraps(f)
    def decorated_function(usuario, *args, **kwargs):
        if usuario.tipo != 'admin':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('usuarios.usuarios', key=usuario.key))
        return f(usuario, *args, **kwargs)
    return decorated_function

"""
TimbuMuscle - Plataforma de Treinos Personalizados
Ponto de entrada da aplicação Flask.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, url_for, redirect
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from db import db
from limiter_ext import limiter

csrf = CSRFProtect()

# Carregar variaveis de ambiente do arquivo .env
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=dotenv_path, override=True)


def create_app():
    """Factory pattern para criar a aplicação Flask."""
    app = Flask(__name__)

    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'altere-esta-chave-em-producao')
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        database_url = f'sqlite:///{os.path.join(instance_path, "users.db")}'
    elif database_url.startswith('sqlite:///') and not database_url.startswith('sqlite:////'):
        database_path = database_url.removeprefix('sqlite:///')
        if database_path.startswith('instance/'):
            database_path = database_path.removeprefix('instance/')
        database_url = f'sqlite:///{os.path.join(instance_path, database_path)}'

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # CSRF
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = app.config['SECRET_KEY']

    # Inicializar extensoes
    csrf.init_app(app)
    db.init_app(app)

    # Flask-Migrate (Alembic)
    Migrate(app, db)

    # Flask-Limiter
    limiter.init_app(app)

    # Registrar blueprints
    from blueprints.auth import auth_bp
    from blueprints.usuarios import usuarios_bp
    from blueprints.profissional import profissional_bp
    from blueprints.suporte import suporte_bp
    from blueprints.chat import chat_bp
    from blueprints.admin import admin_bp
    from blueprints.treinos import treinos_bp
    from blueprints.formulario import formulario_bp, historico_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(profissional_bp)
    app.register_blueprint(suporte_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(treinos_bp)
    app.register_blueprint(formulario_bp)
    app.register_blueprint(historico_bp)

    @app.errorhandler(404)
    def not_found(e):
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Rota não encontrada'}), 404
        return redirect(url_for('auth.homepage'))

    @app.errorhandler(500)
    def server_error(e):
        from flask import flash
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Erro interno do servidor'}), 500
        flash('Ocorreu um erro inesperado. Tente novamente.', 'erro')
        return redirect(url_for('auth.homepage'))

    @app.cli.command('init-db')
    def init_db():
        """CLI: cria todas as tabelas do banco."""
        with app.app_context():
            db.create_all()
        print('Banco de dados inicializado.')

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)

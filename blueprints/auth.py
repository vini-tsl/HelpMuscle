"""
TimbuMuscle - Blueprint de Autenticação
Login, registro, recuperação de senha.
"""
import os
import secrets
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash
from db import db
from models import Usuario
from sqlalchemy.exc import IntegrityError
from limiter_ext import limiter

auth_bp = Blueprint('auth', __name__)


def enviar_codigo_por_email(destinatario, codigo):
    remetente = os.environ.get('EMAIL_USER', 'timbumuscle@gmail.com')
    senha = os.environ.get('EMAIL_PASSWORD', '')

    mensagem = MIMEMultipart("alternative")
    mensagem["Subject"] = "Código de verificação - TimbuMuscle"
    mensagem["From"] = remetente
    mensagem["To"] = destinatario
    mensagem.attach(MIMEText(
        f"""<html><body>
            <h2>Seu código de verificação</h2>
            <p>Use o código abaixo para redefinir sua senha:</p>
            <h1 style="color: #FF4B2B;">{codigo}</h1>
            <p>Se você não solicitou isso, ignore este email.</p>
        </body></html>""",
        "html"
    ))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.sendmail(remetente, destinatario, mensagem.as_string())
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao enviar email: {e}")
        return False


# --------- Páginas públicas ---------

@auth_bp.route("/")
def homepage():
    return render_template("public/index.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.verificar_senha(senha):
            session['user_key'] = usuario.key
            usuario.online = True
            db.session.commit()

            if usuario.tipo == "profissional":
                return redirect(url_for("profissional.profissional", key=usuario.key))
            return redirect(url_for("usuarios.usuarios", key=usuario.key))

        flash("Credenciais inválidas.", "erro")

    return render_template("public/login.html")


@auth_bp.route("/logout")
def logout():
    """Encerra a sessão do usuário."""
    user_key = session.get('user_key')
    if user_key:
        usuario = Usuario.query.filter_by(key=user_key).first()
        if usuario:
            usuario.online = False
            db.session.commit()
    session.clear()
    return redirect(url_for("auth.homepage"))


@auth_bp.route("/registrar", methods=["POST"])
def registrar():
    # TODO: Implementar confirmacao de email quando EMAIL_USER/EMAIL_PASSWORD estiver configurado
    key = secrets.token_hex(6)
    nome = request.form.get("nome")
    email = request.form.get("email")
    senha = request.form.get("senha")
    telefone = request.form.get("telefone")

    if Usuario.query.filter_by(nome=nome).first():
        flash("Nome de usuário já cadastrado.", "erro")
        return redirect(url_for("auth.login"))

    if Usuario.query.filter_by(email=email).first():
        flash("Email já cadastrado.", "erro")
        return redirect(url_for("auth.login"))

    if telefone and Usuario.query.filter_by(telefone=telefone).first():
        flash("Telefone já cadastrado.", "erro")
        return redirect(url_for("auth.login"))

    while Usuario.query.filter_by(key=key).first():
        key = secrets.token_hex(6)

    novo_usuario = Usuario(
        key=key,
        nome=nome,
        email=email,
        senha_hash="",  # Será sobrescrito por set_senha
        telefone=telefone,
    )
    novo_usuario.set_senha(senha)

    try:
        db.session.add(novo_usuario)
        db.session.commit()
        flash("Cadastro realizado com sucesso! Faça login.", "sucesso")
        return redirect(url_for("auth.login"))
    except IntegrityError:
        db.session.rollback()
        flash("Erro ao cadastrar. Tente novamente.", "erro")
        return redirect(url_for("auth.login"))


# --------- Recuperação de senha ---------

@auth_bp.route("/esq_senha", methods=["GET", "POST"])
@limiter.limit("3 per hour", methods=["POST"])
def esq_senha():
    if request.method == "POST":
        email = request.form.get("email")
        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario:
            return jsonify({"error": "Email não cadastrado."}), 404

        codigo = f"{random.randint(100000, 999999)}"
        session["email_reset"] = email
        session["codigo_reset"] = codigo

        if not enviar_codigo_por_email(email, codigo):
            flash("Falha ao enviar email. Tente novamente.", "erro")
            return redirect(url_for("auth.esq_senha"))

        return jsonify({"message": "Código enviado para o email."})

    return render_template("public/esq_senha.html")


@auth_bp.route("/verificar_codigo", methods=["POST"])
def verificar_codigo():
    codigo_enviado = request.form.get("codigo")
    codigo_armazenado = session.get("codigo_reset")

    if not codigo_armazenado:
        return jsonify({"error": "Nenhum código gerado para esta sessão."}), 400

    if codigo_enviado == codigo_armazenado:
        session["codigo_verificado"] = True
        return jsonify({"message": "Código confirmado."})

    return jsonify({"error": "Código inválido."}), 400


@auth_bp.route("/alterar_senha", methods=["POST"])
def alterar_senha():
    if not session.get("codigo_verificado"):
        return jsonify({"error": "Código não verificado."}), 400

    nova_senha = request.form.get("nova_senha")
    confirmar_senha = request.form.get("confirmar_senha")
    email = session.get("email_reset")

    if not nova_senha or not confirmar_senha:
        return jsonify({"error": "Preencha todos os campos."}), 400
    if nova_senha != confirmar_senha:
        return jsonify({"error": "Senhas não conferem."}), 400
    if len(nova_senha) < 6:
        return jsonify({"error": "Senha deve ter ao menos 6 caracteres."}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        return jsonify({"error": "Usuário não encontrado."}), 404

    usuario.set_senha(nova_senha)
    db.session.commit()

    session.pop("codigo_reset", None)
    session.pop("codigo_verificado", None)
    session.pop("email_reset", None)

    return jsonify({"message": "Senha alterada com sucesso."})

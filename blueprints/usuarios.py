"""
TimbuMuscle - Blueprint do Usuário
Rotas do painel do aluno: dashboard, formulário, treinos, perfil.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import Usuario, Treino
from db import db
from middleware.auth import login_required, profissional_required

usuarios_bp = Blueprint('usuarios', __name__)


@usuarios_bp.route("/usuarios/<key>")
@login_required
def usuarios(usuario, key=None):
    return render_template("user/usuarios.html", key=usuario.key, user=usuario)


@usuarios_bp.route("/formulario/<key>")
@login_required
def formulario(usuario, key=None):
    return render_template("user/formulario.html", key=usuario.key, user=usuario)


@usuarios_bp.route("/treino/<key>")
@login_required
def mostrar_treinos(usuario, key=None):
    return redirect(url_for('treinos.mostrar_treinos', key=usuario.key))


@usuarios_bp.route("/perfil/<key>", methods=['GET', 'POST'])
@login_required
def perfil(usuario, key=None):
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        telefone = request.form.get('telefone', '').strip()
        idade = request.form.get('idade', type=int)
        peso = request.form.get('peso', type=float)
        altura = request.form.get('altura', type=float)

        if nome and nome != usuario.nome:
            if Usuario.query.filter_by(nome=nome).first():
                flash('Nome já está em uso.', 'erro')
                return redirect(url_for('usuarios.perfil', key=usuario.key))
            usuario.nome = nome

        if email and email != usuario.email:
            if Usuario.query.filter_by(email=email).first():
                flash('Email já está cadastrado.', 'erro')
                return redirect(url_for('usuarios.perfil', key=usuario.key))
            usuario.email = email

        if telefone and telefone != usuario.telefone:
            if Usuario.query.filter_by(telefone=telefone).first():
                flash('Telefone já está cadastrado.', 'erro')
                return redirect(url_for('usuarios.perfil', key=usuario.key))
            usuario.telefone = telefone

        usuario.idade = idade
        usuario.peso = peso
        usuario.altura = altura

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'sucesso')
        return redirect(url_for('usuarios.perfil', key=usuario.key))

    return render_template("user/perfil.html", key=usuario.key, user=usuario)


@usuarios_bp.route("/perfil/alterar-senha/<key>", methods=['POST'])
@login_required
def alterar_senha_perfil(usuario, key=None):
    senha_atual = request.form.get('senha_atual')
    nova_senha = request.form.get('nova_senha')
    confirmar_senha = request.form.get('confirmar_senha')

    if not usuario.verificar_senha(senha_atual):
        flash('Senha atual incorreta.', 'erro')
        return redirect(url_for('usuarios.perfil', key=usuario.key))

    if nova_senha != confirmar_senha:
        flash('As novas senhas nao conferem.', 'erro')
        return redirect(url_for('usuarios.perfil', key=usuario.key))

    if len(nova_senha) < 6:
        flash('A nova senha deve ter ao menos 6 caracteres.', 'erro')
        return redirect(url_for('usuarios.perfil', key=usuario.key))

    usuario.set_senha(nova_senha)
    db.session.commit()
    flash('Senha alterada com sucesso!', 'sucesso')
    return redirect(url_for('usuarios.perfil', key=usuario.key))


@usuarios_bp.route("/chat_nutri/<key>")
@login_required
def chat_nutri(usuario, key=None):
    return redirect(url_for('suporte.suporte', key=usuario.key))


@usuarios_bp.route("/chat_personal/<key>")
@login_required
def chat_personal(usuario, key=None):
    return redirect(url_for('suporte.suporte', key=usuario.key))


@usuarios_bp.route('/executar-treino/<int:treino_id>/<key>')
@login_required
def executar_treino(usuario, treino_id, key=None):
    treino = Treino.query.get(treino_id)
    if not treino or treino.aluno_id != usuario.id:
        return "Treino não encontrado", 404
    return render_template('user/executar_treino.html',
                           user=usuario,
                           key=usuario.key,
                           treino=treino)

"""
TimbuMuscle - Blueprint do Profissional
Painel do personal trainer: visao geral, alunos, estatisticas.
"""
from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from db import db
from models import Usuario, Treino, Progresso
from middleware.auth import login_required, profissional_required

profissional_bp = Blueprint('profissional', __name__)

ALUNOS_POR_PAGINA = 15


@profissional_bp.route("/profissional/<key>")
@login_required
@profissional_required
def profissional(usuario, key=None):
    alunos_ativos = Usuario.query.filter_by(tipo='usuario').count()
    treinos_ativos = Treino.query.filter_by(status='ativo').count()

    return render_template('admin/profissional.html',
                           key=usuario.key,
                           user=usuario,
                           alunos=[],  # carregado via JS API
                           alunos_ativos=alunos_ativos,
                           treinos_ativos=treinos_ativos)


@profissional_bp.route('/api/estatisticas/<key>')
@login_required
@profissional_required
def api_estatisticas(usuario, key=None):
    total_alunos = Usuario.query.filter_by(tipo='usuario').count()
    treinos_ativos = Treino.query.filter_by(status='ativo').count()
    alunos_com_treino = Usuario.query.filter_by(tipo='usuario') \
        .join(Treino).filter(Treino.status == 'ativo').count()

    return jsonify({
        'total_alunos': total_alunos,
        'alunos_ativos': alunos_com_treino,
        'treinos_ativos': treinos_ativos,
        'alunos_inativos': total_alunos - alunos_com_treino,
        'chats_ativos': 5,
    })


@profissional_bp.route('/api/alunos/<key>')
@login_required
@profissional_required
def api_alunos(usuario, key=None):
    pagina = request.args.get('pagina', 1, type=int)
    paginacao = Usuario.query \
        .filter_by(tipo='usuario') \
        .order_by(Usuario.nome) \
        .paginate(page=pagina, per_page=ALUNOS_POR_PAGINA, error_out=False)

    alunos_data = []
    for aluno in paginacao.items:
        treino_ativo = Treino.query.filter_by(aluno_id=aluno.id, status='ativo').first()
        progresso = Progresso.query.filter_by(aluno_id=aluno.id) \
            .order_by(Progresso.data_registro.desc()).first()

        ultimo_acesso = 'Hoje'
        if aluno.ultimo_acesso:
            from datetime import datetime
            diff = (datetime.utcnow() - aluno.ultimo_acesso).days
            if diff == 0:
                ultimo_acesso = 'Hoje'
            elif diff == 1:
                ultimo_acesso = 'Ontem'
            else:
                ultimo_acesso = aluno.ultimo_acesso.strftime('%d/%m')

        alunos_data.append({
            'id': aluno.id,
            'nome': aluno.nome,
            'treino': treino_ativo.nome if treino_ativo else 'Sem treino',
            'nivel': treino_ativo.tipo if treino_ativo else '-',
            'progresso': progresso.porcentagem if progresso else 0,
            'status': 'Ativo' if treino_ativo else 'Inativo',
            'ultimo_acesso': ultimo_acesso,
        })

    return jsonify({
        'alunos': alunos_data,
        'pagina': pagina,
        'total_paginas': paginacao.pages,
        'total_alunos': paginacao.total,
    })

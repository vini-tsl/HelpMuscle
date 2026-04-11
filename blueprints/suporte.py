"""
TimbuMuscle - Blueprint de Suporte
Criação e gestão de chamados de suporte.
"""
from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from models import Usuario, ChamadoSuporte, MensagemSuporte
from db import db
from datetime import datetime
from sqlalchemy import desc

suporte_bp = Blueprint('suporte', __name__)


def buscar_usuario_por_key(key):
    return Usuario.query.filter_by(key=key).first()


@suporte_bp.route("/suporte/<key>")
def suporte(key):
    user = buscar_usuario_por_key(key)
    if user is None:
        return redirect(url_for('auth.login'))

    chamado_ativo = ChamadoSuporte.query.filter_by(
        usuario_id=user.id,
        status='aberto',
    ).first()

    return render_template("user/suporte.html", key=key, user=user, chamado_ativo=chamado_ativo)


@suporte_bp.route('/api/criar-chamado', methods=['POST'])
def criar_chamado():
    data = request.get_json()
    key = data.get('key')
    tipo = data.get('tipo')

    user = buscar_usuario_por_key(key)
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'})

    chamado_existente = ChamadoSuporte.query.filter_by(
        usuario_id=user.id,
        status='aberto',
    ).first()

    if chamado_existente:
        return jsonify({'success': False, 'message': 'Já existe um chamado em aberto'})

    profissional = _encontrar_profissional_disponivel()

    novo_chamado = ChamadoSuporte(
        usuario_id=user.id,
        profissional_id=profissional.id if profissional else None,
        tipo=tipo,
        status='aberto',
    )
    db.session.add(novo_chamado)
    db.session.commit()

    return jsonify({
        'success': True,
        'chamado_id': novo_chamado.id,
        'message': 'Chamado criado com sucesso',
    })


def _encontrar_profissional_disponivel():
    profissionais_online = Usuario.query \
        .filter_by(tipo='profissional', online=True).all()
    if profissionais_online:
        return profissionais_online[0]

    return Usuario.query.filter_by(tipo='profissional') \
        .order_by(desc(Usuario.ultimo_acesso)).first()


# --------- Profissional: visão de chamados ---------

@suporte_bp.route("/suporte_profissional/<key>")
def suporte_pro(key):
    user = Usuario.query.filter_by(key=key).first()
    if not user or user.tipo != 'profissional':
        return redirect(url_for('auth.login'))
    return render_template("admin/suporte_profissional.html", key=key, user=user)


@suporte_bp.route('/api/chamados-profissional/<key>')
def api_chamados_profissional(key):
    user = Usuario.query.filter_by(key=key).first()
    if not user or user.tipo != 'profissional':
        return jsonify({'success': False, 'message': 'Acesso não autorizado'})

    chamados = ChamadoSuporte.query.filter_by(profissional_id=user.id) \
        .order_by(ChamadoSuporte.data_abertura.desc()).all()

    chamados_data = []
    for chamado in chamados:
        ultima_msg = MensagemSuporte.query.filter_by(chamado_id=chamado.id) \
            .order_by(MensagemSuporte.data_envio.desc()).first()

        nao_lidas = MensagemSuporte.query.filter_by(
            chamado_id=chamado.id,
            lida=False,
        ).filter(MensagemSuporte.remetente_id != user.id).count()

        mensagens = MensagemSuporte.query.filter_by(chamado_id=chamado.id) \
            .order_by(MensagemSuporte.data_envio).all()

        chamados_data.append({
            'id': chamado.id,
            'usuario': {
                'nome': chamado.usuario.nome,
                'telefone': chamado.usuario.telefone,
            },
            'status': chamado.status,
            'ultima_mensagem': ultima_msg.mensagem if ultima_msg else 'Nenhuma mensagem',
            'data_ultima_mensagem': ultima_msg.data_envio.strftime('%H:%M') if ultima_msg else chamado.data_abertura.strftime('%H:%M'),
            'mensagens_nao_lidas': nao_lidas,
            'mensagens': [
                {
                    'conteudo': msg.mensagem,
                    'remetente_id': msg.remetente_id,
                    'data_envio': msg.data_envio.strftime('%H:%M'),
                } for msg in mensagens
            ],
        })

    return jsonify({'success': True, 'chamados': chamados_data})


@suporte_bp.route('/api/enviar-mensagem-profissional', methods=['POST'])
def enviar_mensagem_profissional():
    data = request.get_json()
    key = data.get('key')
    chamado_id = data.get('chamado_id')
    mensagem = data.get('mensagem')

    user = Usuario.query.filter_by(key=key).first()
    chamado = ChamadoSuporte.query.get(chamado_id)

    if not user or not chamado:
        return jsonify({'success': False, 'message': 'Usuário ou chamado não encontrado'})
    if chamado.status == 'fechado':
        return jsonify({'success': False, 'message': 'Este chamado está fechado'})
    if chamado.profissional_id != user.id:
        return jsonify({'success': False, 'message': 'Acesso não autorizado'})

    nova_mensagem = MensagemSuporte(
        chamado_id=chamado_id,
        remetente_id=user.id,
        mensagem=mensagem,
    )
    db.session.add(nova_mensagem)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Mensagem enviada'})


@suporte_bp.route('/api/fechar-chamado-profissional', methods=['POST'])
def fechar_chamado_profissional():
    data = request.get_json()
    key = data.get('key')
    chamado_id = data.get('chamado_id')

    user = Usuario.query.filter_by(key=key).first()
    chamado = ChamadoSuporte.query.get(chamado_id)

    if not user or not chamado:
        return jsonify({'success': False, 'message': 'Usuário ou chamado não encontrado'})
    if user.tipo != 'profissional' or user.id != chamado.profissional_id:
        return jsonify({'success': False, 'message': 'Acesso não autorizado'})
    if chamado.status == 'fechado':
        return jsonify({'success': False, 'message': 'Chamado já está fechado'})

    chamado.status = 'fechado'
    chamado.data_fechamento = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'message': 'Chamado fechado com sucesso'})


@suporte_bp.route('/api/marcar-mensagens-lidas', methods=['POST'])
def marcar_mensagens_lidas():
    data = request.get_json()
    key = data.get('key')
    chamado_id = data.get('chamado_id')

    user = Usuario.query.filter_by(key=key).first()
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'})

    mensagens_nao_lidas = MensagemSuporte.query.filter_by(
        chamado_id=chamado_id,
        lida=False,
    ).filter(MensagemSuporte.remetente_id != user.id).all()

    for msg in mensagens_nao_lidas:
        msg.lida = True

    db.session.commit()
    return jsonify({'success': True, 'message': 'Mensagens marcadas como lidas'})

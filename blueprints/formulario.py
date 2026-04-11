"""
TimbuMuscle - Blueprint do Formulário
Coleta dados do aluno e gera treinos usando services/treino_engine.py.
"""
from flask import Blueprint, jsonify, request, redirect, url_for, render_template
from db import db
from models import Usuario, HistoricoTreino, Treino, SerieExercicioExecutada, MedidaCorporal
from datetime import datetime
from services.treino_engine import gerar_treinos, validar_treino
from middleware.auth import login_required

formulario_bp = Blueprint('formulario', __name__)
historico_bp = Blueprint('historico', __name__)


@historico_bp.route('/historico/<key>')
@login_required
def historico(usuario, key=None):
    return render_template('user/historico.html', user=usuario, key=usuario.key)


@formulario_bp.route('/formulario/<key>')
@login_required
def formulario(usuario, key=None):
    return render_template('user/formulario.html', user=usuario, key=key)


@formulario_bp.route('/api/salvar-formulario', methods=['POST'])
def salvar_formulario():
    """Salva dados do questionário e gera treinos personalizados."""
    try:
        data = request.get_json()
        key = data.get('key')

        usuario = Usuario.query.filter_by(key=key).first()
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'})

        mapeamento_objetivos = {
            'massa': 'hipertrofia',
            'definicao': 'definicao',
            'saude': 'hipertrofia',
            'forca': 'forca',
            'estetico': 'definicao',
        }

        tempo_str = data.get('tempo', '60')
        try:
            tempo_treino = 90 if tempo_str == 'mais' else int(tempo_str)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Tempo de treino inválido.'})
        if tempo_treino not in (90,) and not (10 <= tempo_treino <= 300):
            return jsonify({'success': False, 'message': 'Tempo de treino deve estar entre 10 e 300 minutos.'})

        # Validação de idade
        idade = data.get('idade')
        if idade is not None:
            try:
                idade = int(idade)
                if not (10 <= idade <= 120):
                    return jsonify({'success': False, 'message': 'Idade inválida.'})
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Idade inválida.'})

        # Validação de peso
        peso = data.get('peso')
        if peso is not None:
            try:
                peso = float(peso)
                if not (20 <= peso <= 500):
                    return jsonify({'success': False, 'message': 'Peso inválido.'})
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Peso inválido.'})

        # Validação de altura
        altura = data.get('altura')
        if altura is not None:
            try:
                altura = float(altura)
                if not (100 <= altura <= 250):
                    return jsonify({'success': False, 'message': 'Altura inválida.'})
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Altura inválida.'})

        try:
            frequencia = int(data.get('frequencia', 3))
        except (ValueError, TypeError):
            frequencia = 3

        usuario.objetivo = mapeamento_objetivos.get(data.get('objetivo'), 'hipertrofia')
        usuario.nivel_experiencia = data.get('nivel', 'iniciante')
        usuario.dias_treino_semana = frequencia
        usuario.tempo_treino_dia = tempo_treino
        usuario.restricoes_medicas = data.get('lesao', 'nao')
        usuario.formulario_preenchido = True
        usuario.data_formulario = datetime.utcnow()

        areas_foco = data.get('foco', [])
        if isinstance(areas_foco, list) and areas_foco:
            usuario.restricoes_medicas += f"\nÁreas de foco: {', '.join(areas_foco)}"

        db.session.commit()

        # Gera treinos via serviço centralizado
        treinos_gerados = gerar_treinos(usuario)

        return jsonify({
            'success': True,
            'message': f'Formulário salvo! {len(treinos_gerados)} treinos gerados.',
            'treinos_gerados': len(treinos_gerados),
            'redirect_url': url_for('usuarios.mostrar_treinos', key=key),
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})


# --------- Execução e ajuste de treinos ---------

@formulario_bp.route('/api/registrar-execucao-treino', methods=['POST'])
def registrar_execucao_treino():
    """Registra a execucao de um treino com series detalhadas."""
    try:
        data = request.get_json()
        key = data.get('key')

        usuario = Usuario.query.filter_by(key=key).first()
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuario nao encontrado'})

        historico = HistoricoTreino(
            usuario_id=usuario.id,
            treino_id=data.get('treino_id'),
            duracao_minutos=data.get('duracao_minutos'),
            dificuldade_percebida=data.get('dificuldade_percebida'),
            feedback_usuario=data.get('feedback', ''),
        )
        historico.ajuste_recomendado = _analisar_desempenho(
            data.get('treino_id'), data.get('duracao_minutos'), data.get('dificuldade_percebida')
        )

        db.session.add(historico)
        db.session.flush()

        # Salvar series detalhadas de cada exercicio
        series_data = data.get('series', [])
        for serie in series_data:
            serie_registro = SerieExercicioExecutada(
                historico_id=historico.id,
                exercicio_treino_id=serie['exercicio_treino_id'],
                serie_numero=serie.get('serie_numero', 1),
                peso_kg=serie.get('peso_kg', 0),
                reps_feitas=serie.get('reps_feitas', 0),
                concluida=serie.get('concluida', True),
            )
            db.session.add(serie_registro)

        db.session.commit()

        return jsonify({
            'success': True,
            'ajuste_recomendado': historico.ajuste_recomendado,
            'message': 'Treino registrado com sucesso!',
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@formulario_bp.route('/api/registrar-medida-corporal', methods=['POST'])
def registrar_medida_corporal():
    """Registra medidas corporais do usuario (peso, medidas, etc)."""
    try:
        data = request.get_json()
        usuario = Usuario.query.filter_by(key=data.get('key')).first()
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuario nao encontrado'})

        medida = MedidaCorporal(
            usuario_id=usuario.id,
            peso_kg=data.get('peso_kg'),
            gordura_corporal=data.get('gordura_corporal'),
            braco_cm=data.get('braco_cm'),
            peito_cm=data.get('peito_cm'),
            cintura_cm=data.get('cintura_cm'),
            coxa_cm=data.get('coxa_cm'),
            panturrilha_cm=data.get('panturrilha_cm'),
        )
        db.session.add(medida)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Medidas registradas com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@formulario_bp.route('/api/historico-treinos', methods=['GET'])
def api_historico_treinos():
    """Retorna historico de treinos executados do usuario."""
    key = request.args.get('key')
    usuario = Usuario.query.filter_by(key=key).first()
    if not usuario:
        return jsonify({'success': False, 'message': 'Usuario nao encontrado'})

    historicos = HistoricoTreino.query \
        .filter_by(usuario_id=usuario.id) \
        .order_by(HistoricoTreino.data_execucao.desc()) \
        .all()

    resultado = []
    for h in historicos:
        treino = Treino.query.get(h.treino_id)
        resultado.append({
            'id': h.id,
            'treino_nome': treino.nome if treino else 'Treino removido',
            'data': h.data_execucao.strftime('%d/%m/%Y %H:%M'),
            'duracao_min': h.duracao_minutos or 0,
            'dificuldade': h.dificuldade_percebida or '-',
            'feedback': h.feedback_usuario,
            'num_series': len(h.serie_exercicios),
        })

    return jsonify({'success': True, 'historico': resultado})


@formulario_bp.route('/api/evolucao-peso', methods=['GET'])
def api_evolucao_peso():
    """Retorna evolucao de peso e medidas corporais."""
    key = request.args.get('key')
    usuario = Usuario.query.filter_by(key=key).first()
    if not usuario:
        return jsonify({'success': False, 'message': 'Usuario nao encontrado'})

    medidas = MedidaCorporal.query \
        .filter_by(usuario_id=usuario.id) \
        .filter(MedidaCorporal.peso_kg.isnot(None)) \
        .order_by(MedidaCorporal.data_registro.asc()) \
        .all()

    resultado = [{
        'data': m.data_registro.strftime('%d/%m'),
        'peso_kg': m.peso_kg,
        'gordura_corporal': m.gordura_corporal,
    } for m in medidas]

    return jsonify({'success': True, 'evolucao': resultado})


@formulario_bp.route('/api/aplicar-ajuste-treino', methods=['POST'])
def aplicar_ajuste_treino():
    """Aplica ajustes automáticos nos treinos baseado no desempenho."""
    try:
        data = request.get_json()
        key = data.get('key')
        treino_id = data.get('treino_id')
        acao = data.get('acao')

        usuario = Usuario.query.filter_by(key=key).first()
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'})

        treino = Treino.query.get(treino_id)
        if not treino:
            return jsonify({'success': False, 'message': 'Treino não encontrado'})

        for exercicio in treino.exercicios_treino:
            if acao == 'aumentar':
                if exercicio.series < 5:
                    exercicio.series += 1
                reps = exercicio.repeticoes.split('-')
                if len(reps) == 2:
                    exercicio.repeticoes = f"{max(int(reps[0]) - 2, 6)}-{max(int(reps[1]) - 2, 8)}"

            elif acao == 'reduzir':
                if exercicio.series > 2:
                    exercicio.series -= 1
                reps = exercicio.repeticoes.split('-')
                if len(reps) == 2:
                    exercicio.repeticoes = f"{int(reps[0]) + 2}-{int(reps[1]) + 2}"

        db.session.commit()
        return jsonify({'success': True, 'message': f'Intensidade ajustada para {acao}!'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# --------- Helpers internos ---------

def _analisar_desempenho(treino_id, duracao, dificuldade):
    """Analisa desempenho e sugere ajuste."""
    treino = Treino.query.get(treino_id)
    if not treino:
        return "manter"

    num_exercicios = len(treino.exercicios)
    tempo_esperado = num_exercicios * 15

    if dificuldade in ['muito_facil', 'facil'] and duracao < tempo_esperado * 0.7:
        return "aumentar"
    elif dificuldade == 'muito_dificil' and duracao > tempo_esperado * 1.3:
        return "reduzir"
    return "manter"

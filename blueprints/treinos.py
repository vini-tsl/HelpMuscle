"""
TimbuMuscle - Blueprint de Treinos
Endpoints API para exercícios e listagem de treinos.
A lógica de geração foi extraída para services/treino_engine.py.
"""
from flask import Blueprint, jsonify, request, render_template
from models import (
    CatalogoExercicio, Treino, Progresso, Usuario,
    HistoricoTreino, SerieExercicioExecutada, ExercicioTreino
)
from services.treino_engine import gerar_treinos
from middleware.auth import login_required

treinos_bp = Blueprint('treinos', __name__)


def _calcular_ultima_execucao(exercicio_treino_id):
    """Retorna dados da ultima execucao de um exercicio."""
    ultima_serie = SerieExercicioExecutada.query \
        .filter_by(exercicio_treino_id=exercicio_treino_id) \
        .join(HistoricoTreino) \
        .order_by(HistoricoTreino.data_execucao.desc()) \
        .first()
    if not ultima_serie:
        return None
    historico = HistoricoTreino.query.get(ultima_serie.historico_id)
    return {
        'data': historico.data_execucao.strftime('%d/%m') if historico else '—',
        'peso_kg': ultima_serie.peso_kg or 0,
        'reps_feitas': ultima_serie.reps_feitas or 0,
    }


def _sugerir_progressao(exercicio_treino, ultima_exec):
    """Compara meta com ultima execucao e sugere acao."""
    if not ultima_exec:
        return 'primeira_vez', None

    reps_meta = exercicio_treino.repeticoes
    if '-' in str(reps_meta):
        partes = str(reps_meta).split('-')
        meta_top = int(partes[1])
    else:
        meta_top = int(reps_meta)

    peso_meta = ultima_exec.get('peso_kg', 0)
    reps_feitas = ultima_exec.get('reps_feitas', 0)

    if reps_feitas >= meta_top + 2 and reps_feitas > 0:
        return 'aumentar_peso', {
            'anterior': f'{peso_meta}kg x {reps_feitas}',
            'sugestao': f'+2.5kg (tente {peso_meta + 2.5}kg)',
        }
    elif reps_feitas >= meta_top and reps_feitas > 0:
        return 'manter_e_voltear', {
            'anterior': f'{peso_meta}kg x {reps_feitas}',
            'sugestao': 'Repita ate conseguir +2 reps',
        }
    elif reps_feitas < meta_top - 3 and reps_feitas > 0:
        return 'reduzir_peso', {
            'anterior': f'{peso_meta}kg x {reps_feitas}',
            'sugestao': f'-2.5kg (tente {max(peso_meta - 2.5, 0)}kg)',
        }
    return 'no_rumo', {
        'anterior': f'{peso_meta}kg x {reps_feitas}',
        'sugestao': 'Continuar progredindo',
    }


@treinos_bp.route('/treinos/<key>')
@login_required
def mostrar_treinos(usuario, key=None):
    """Lista treinos do usuário com progresso e sugestao de progressao."""

    pagina = request.args.get('pagina', 1, type=int)
    paginacao = Treino.query.filter_by(aluno_id=usuario.id) \
        .order_by(Treino.ordem) \
        .paginate(page=pagina, per_page=10, error_out=False)
    treinos = paginacao.items
    progressos = {}
    sugestoes = {}
    for treino in treinos:
        progresso = Progresso.query.filter_by(
            aluno_id=usuario.id, treino_id=treino.id
        ).first()
        progressos[treino.id] = progresso.porcentagem if progresso else 0

        # Calcula sugestao para cada exercicio do treino
        treino_sugestoes = []
        for ex in treino.exercicios:
            ultima = _calcular_ultima_execucao(ex.id)
            status, detalhe = _sugerir_progressao(ex, ultima)
            treino_sugestoes.append({
                'exercicio_id': ex.id,
                'nome': ex.catalogo.nome if ex.catalogo else 'Exercicio',
                'meta': f'{ex.series}x{ex.repeticoes}',
                'ultima': ultima,
                'status': status,
                'detalhe': detalhe,
            })
        sugestoes[treino.id] = treino_sugestoes

    return render_template('user/treinos.html',
                           user=usuario,
                           key=key,
                           treinos=treinos,
                           paginacao=paginacao,
                           progressos=progressos,
                           sugestoes=sugestoes)


@treinos_bp.route('/api/buscar-exercicios')
def buscar_exercicios():
    """API: retorna exercícios do catálogo com filtros opcionais."""
    grupo = request.args.get('grupo')
    nivel = request.args.get('nivel')

    query = CatalogoExercicio.query.filter_by(ativo=True)
    if grupo:
        query = query.filter_by(grupo_muscular=grupo)
    if nivel:
        query = query.filter_by(nivel_dificuldade=nivel)

    exercicios = query.all()

    return jsonify({
        'success': True,
        'exercicios': [{
            'id': ex.id,
            'nome': ex.nome,
            'grupo_muscular': ex.grupo_muscular,
            'equipamento': ex.equipamento,
            'video_url': ex.video_url,
            'instrucoes': ex.instrucoes,
        } for ex in exercicios]
    })

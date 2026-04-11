"""
TimbuMuscle - Motor de geração de treinos
Serviço centralizado para criação, seleção e validação de treinos.
Substitui toda a lógica duplicada entre formulario.py e treinos.py.
"""
from db import db
from models import Treino, ExercicioTreino, CatalogoExercicio, Progresso, HistoricoTreino


# --- Mapeamento de tipo de treino para grupos musculares ---

MAPEAMENTO_GRUPOS = {
    'Treino Peito': ['Peito', 'Ombros', 'Tríceps'],
    'Treino Costas': ['Costas', 'Bíceps'],
    'Treino Pernas': ['Pernas', 'Glúteos', 'Panturrilhas'],
    'Treino Ombros': ['Ombros'],
    'Treino Braços': ['Bíceps', 'Tríceps'],
    'Treino Cardio': ['Cardio'],
    'Full Body A': ['Peito', 'Costas', 'Pernas'],
    'Full Body B': ['Ombros', 'Bíceps', 'Tríceps'],
}

ESTRUTURAS_TREINO = {
    'hipertrofia': {
        2: ['Treino Peito', 'Treino Pernas'],
        3: ['Treino Peito', 'Treino Costas', 'Treino Pernas'],
        4: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Ombros'],
        5: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Ombros', 'Treino Braços'],
        6: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Ombros', 'Treino Braços', 'Treino Cardio'],
    },
    'emagrecimento': {
        2: ['Full Body A', 'Full Body B'],
        3: ['Full Body A', 'Treino Cardio', 'Full Body B'],
        4: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Cardio'],
        5: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Ombros', 'Treino Cardio'],
        6: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Ombros', 'Treino Braços', 'Treino Cardio'],
    },
    'forca': {
        2: ['Treino Peito', 'Treino Pernas'],
        3: ['Treino Peito', 'Treino Costas', 'Treino Pernas'],
        4: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Ombros'],
        5: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Ombros', 'Treino Braços'],
        6: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Ombros', 'Treino Braços', 'Full Body A'],
    },
    'definicao': {
        3: ['Treino Peito', 'Treino Costas', 'Treino Pernas'],
        4: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Cardio'],
        5: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Ombros', 'Treino Cardio'],
        6: ['Treino Peito', 'Treino Costas', 'Treino Pernas', 'Treino Ombros', 'Treino Braços', 'Treino Cardio'],
    },
}

DIAS_SEMANA = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']

PARAMETROS_POR_NIVEL = {
    'iniciante':     {'series': 3, 'repeticoes': '12-15', 'descanso': '60s'},
    'intermediario': {'series': 3, 'repeticoes': '10-12', 'descanso': '75s'},
    'avancado':      {'series': 4, 'repeticoes': '8-10',  'descanso': '90s'},
}

# Ajustes de objetivo que sobrescrevem parâmetros por nível
AJUSTES_OBJETIVO = {
    'forca': {
        'avancado':       {'repeticoes': '4-6',  'descanso': '120s'},
        'intermediario':  {'repeticoes': '6-8',  'descanso': '90s'},
        'iniciante':      {'repeticoes': '6-8',  'descanso': '90s'},
    },
    'emagrecimento': {
        'default': {'repeticoes': '15-20', 'descanso': '45s'},
    },
}

MAX_EXERCICIOS = 5


def limpar_treinos_antigos(usuario_id):
    """Remove treinos, exercícios associados, progressos e histórico de um usuário."""
    treinos_antigos = Treino.query.filter_by(aluno_id=usuario_id).all()
    for treino in treinos_antigos:
        ExercicioTreino.query.filter_by(treino_id=treino.id).delete()
        Progresso.query.filter_by(treino_id=treino.id).delete()
        HistoricoTreino.query.filter_by(treino_id=treino.id).delete()
        db.session.delete(treino)
    db.session.commit()
    return len(treinos_antigos)


def selecionar_exercicios(tipo_treino, nivel, objetivo):
    """Seleciona exercícios do catálogo para um tipo de treino."""
    grupos = MAPEAMENTO_GRUPOS.get(tipo_treino, ['Peito', 'Costas', 'Pernas'])

    selecionados = []
    nomes_vistos = set()

    for grupo in grupos:
        if len(selecionados) >= MAX_EXERCICIOS:
            break

        exercicios = CatalogoExercicio.query.filter_by(
            grupo_muscular=grupo, ativo=True
        ).all()

        for ex in exercicios:
            if ex.nome not in nomes_vistos and len(selecionados) < MAX_EXERCICIOS:
                selecionados.append(ex)
                nomes_vistos.add(ex.nome)

    if not selecionados:
        return []

    # Parametrização base por nível
    params = dict(PARAMETROS_POR_NIVEL.get(nivel, PARAMETROS_POR_NIVEL['iniciante']))

    # Ajuste por objetivo
    ajuste_obj = AJUSTES_OBJETIVO.get(objetivo, {})
    if 'default' in ajuste_obj:
        params.update(ajuste_obj['default'])
    elif nivel in ajuste_obj:
        params.update(ajuste_obj[nivel])

    return [
        {
            'id': ex.id,
            'series': params['series'],
            'repeticoes': params['repeticoes'],
            'descanso': params['descanso'],
        }
        for ex in selecionados
    ]


def gerar_treinos(usuario):
    """Gera todos os treinos para um usuário com base no perfil."""
    objetivo = usuario.objetivo or 'hipertrofia'
    nivel = usuario.nivel_experiencia or 'iniciante'
    dias_semana = usuario.dias_treino_semana or 3

    limpar_treinos_antigos(usuario.id)

    estrutura = ESTRUTURAS_TREINO.get(objetivo, ESTRUTURAS_TREINO['hipertrofia'])
    tipos_treino = estrutura.get(dias_semana, ['Treino Peito', 'Treino Pernas'])

    treinos_criados = []

    for i, tipo in enumerate(tipos_treino):
        if i >= len(DIAS_SEMANA):
            break

        treino = Treino(
            aluno_id=usuario.id,
            nome=tipo,
            tipo=tipo.replace('Treino ', ''),
            descricao=f"Treino personalizado para {objetivo} - Nível {nivel}",
            status='ativo',
            dia_semana=DIAS_SEMANA[i],
            ordem=i + 1,
        )
        db.session.add(treino)
        db.session.flush()

        exercicios = selecionar_exercicios(tipo, nivel, objetivo)

        for j, ex_data in enumerate(exercicios):
            exercicio_treino = ExercicioTreino(
                treino_id=treino.id,
                catalogo_exercicio_id=ex_data['id'],
                series=ex_data['series'],
                repeticoes=ex_data['repeticoes'],
                descanso=ex_data['descanso'],
                ordem=j + 1,
            )
            db.session.add(exercicio_treino)

        treinos_criados.append(treino)

    db.session.commit()
    return treinos_criados


def validar_treino(treino):
    """Valida integridade de um treino (sem duplicatas, máx 5 exercícios)."""
    exercicios = treino.exercicios
    nomes = [ex.catalogo.nome for ex in exercicios]

    if len(exercicios) > MAX_EXERCICIOS:
        return False
    if len(nomes) != len(set(nomes)):
        return False
    return True

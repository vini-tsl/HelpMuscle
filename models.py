from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from db import db


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(30), unique=True, nullable=True)
    tipo = db.Column(db.String(20), nullable=False, default='usuario')
    online = db.Column(db.Boolean, nullable=False, default=False)
    ultimo_acesso = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    idade = db.Column(db.Integer, nullable=True)
    peso = db.Column(db.Float, nullable=True)
    altura = db.Column(db.Float, nullable=True)
    objetivo = db.Column(db.String(30), nullable=True)
    nivel_experiencia = db.Column(db.String(30), nullable=True, default='iniciante')
    dias_treino_semana = db.Column(db.Integer, nullable=True, default=3)
    tempo_treino_dia = db.Column(db.Integer, nullable=True, default=60)
    restricoes_medicas = db.Column(db.Text, nullable=True)
    formulario_preenchido = db.Column(db.Boolean, nullable=False, default=False)
    data_formulario = db.Column(db.DateTime, nullable=True)

    treinos = db.relationship('Treino', back_populates='aluno', cascade='all, delete-orphan')
    progressos = db.relationship('Progresso', back_populates='aluno', cascade='all, delete-orphan')
    historicos = db.relationship('HistoricoTreino', back_populates='usuario', cascade='all, delete-orphan')
    medidas = db.relationship('MedidaCorporal', back_populates='usuario', cascade='all, delete-orphan')
    chamados = db.relationship(
        'ChamadoSuporte', foreign_keys='ChamadoSuporte.usuario_id',
        back_populates='usuario', cascade='all, delete-orphan'
    )
    chamados_atendidos = db.relationship(
        'ChamadoSuporte', foreign_keys='ChamadoSuporte.profissional_id',
        back_populates='profissional'
    )
    mensagens = db.relationship('MensagemSuporte', back_populates='remetente')

    @property
    def progresso(self):
        progresso = max(self.progressos, key=lambda item: item.data_registro, default=None)
        return progresso.porcentagem if progresso else 0

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return bool(self.senha_hash) and check_password_hash(self.senha_hash, senha)


class CatalogoExercicio(db.Model):
    __tablename__ = 'catalogo_exercicios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    grupo_muscular = db.Column(db.String(60), nullable=False, index=True)
    equipamento = db.Column(db.String(120), nullable=True)
    nivel_dificuldade = db.Column(db.String(30), nullable=True, default='iniciante')
    video_url = db.Column(db.String(500), nullable=True)
    instrucoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True, index=True)

    treinos = db.relationship('ExercicioTreino', back_populates='catalogo')


class Treino(db.Model):
    __tablename__ = 'treinos'

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    nome = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(60), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='ativo', index=True)
    dia_semana = db.Column(db.String(20), nullable=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    aluno = db.relationship('Usuario', back_populates='treinos')
    exercicios = db.relationship(
        'ExercicioTreino', back_populates='treino',
        cascade='all, delete-orphan', order_by='ExercicioTreino.ordem'
    )
    progressos = db.relationship('Progresso', back_populates='treino', cascade='all, delete-orphan')
    historicos = db.relationship('HistoricoTreino', back_populates='treino')

    @property
    def exercicios_treino(self):
        return self.exercicios


class ExercicioTreino(db.Model):
    __tablename__ = 'exercicios_treino'

    id = db.Column(db.Integer, primary_key=True)
    treino_id = db.Column(db.Integer, db.ForeignKey('treinos.id'), nullable=False, index=True)
    catalogo_exercicio_id = db.Column(
        db.Integer, db.ForeignKey('catalogo_exercicios.id'), nullable=False
    )
    series = db.Column(db.Integer, nullable=False, default=3)
    repeticoes = db.Column(db.String(20), nullable=False, default='10-12')
    descanso = db.Column(db.String(20), nullable=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)

    treino = db.relationship('Treino', back_populates='exercicios')
    catalogo = db.relationship('CatalogoExercicio', back_populates='treinos')
    series_executadas = db.relationship(
        'SerieExercicioExecutada', back_populates='exercicio_treino',
        cascade='all, delete-orphan'
    )


class Progresso(db.Model):
    __tablename__ = 'progressos'

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    treino_id = db.Column(db.Integer, db.ForeignKey('treinos.id'), nullable=False, index=True)
    porcentagem = db.Column(db.Float, nullable=False, default=0)
    data_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    aluno = db.relationship('Usuario', back_populates='progressos')
    treino = db.relationship('Treino', back_populates='progressos')


class HistoricoTreino(db.Model):
    __tablename__ = 'historico_treinos'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    treino_id = db.Column(db.Integer, db.ForeignKey('treinos.id'), nullable=False, index=True)
    data_execucao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    duracao_minutos = db.Column(db.Integer, nullable=True)
    dificuldade_percebida = db.Column(db.String(30), nullable=True)
    feedback_usuario = db.Column(db.Text, nullable=True)
    ajuste_recomendado = db.Column(db.String(30), nullable=True, default='manter')

    usuario = db.relationship('Usuario', back_populates='historicos')
    treino = db.relationship('Treino', back_populates='historicos')
    serie_exercicios = db.relationship(
        'SerieExercicioExecutada', back_populates='historico',
        cascade='all, delete-orphan'
    )


class SerieExercicioExecutada(db.Model):
    __tablename__ = 'series_exercicios_executadas'

    id = db.Column(db.Integer, primary_key=True)
    historico_id = db.Column(db.Integer, db.ForeignKey('historico_treinos.id'), nullable=False, index=True)
    exercicio_treino_id = db.Column(db.Integer, db.ForeignKey('exercicios_treino.id'), nullable=False)
    serie_numero = db.Column(db.Integer, nullable=False, default=1)
    peso_kg = db.Column(db.Float, nullable=True, default=0)
    reps_feitas = db.Column(db.Integer, nullable=True, default=0)
    concluida = db.Column(db.Boolean, nullable=False, default=True)

    historico = db.relationship('HistoricoTreino', back_populates='serie_exercicios')
    exercicio_treino = db.relationship('ExercicioTreino', back_populates='series_executadas')


class MedidaCorporal(db.Model):
    __tablename__ = 'medidas_corporais'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    data_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    peso_kg = db.Column(db.Float, nullable=True)
    gordura_corporal = db.Column(db.Float, nullable=True)
    braco_cm = db.Column(db.Float, nullable=True)
    peito_cm = db.Column(db.Float, nullable=True)
    cintura_cm = db.Column(db.Float, nullable=True)
    coxa_cm = db.Column(db.Float, nullable=True)
    panturrilha_cm = db.Column(db.Float, nullable=True)

    usuario = db.relationship('Usuario', back_populates='medidas')


class ChamadoSuporte(db.Model):
    __tablename__ = 'chamados_suporte'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True, index=True)
    tipo = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='aberto', index=True)
    data_abertura = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_fechamento = db.Column(db.DateTime, nullable=True)

    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], back_populates='chamados')
    profissional = db.relationship(
        'Usuario', foreign_keys=[profissional_id], back_populates='chamados_atendidos'
    )
    mensagens = db.relationship(
        'MensagemSuporte', back_populates='chamado', cascade='all, delete-orphan',
        order_by='MensagemSuporte.data_envio'
    )


class MensagemSuporte(db.Model):
    __tablename__ = 'mensagens_suporte'

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamados_suporte.id'), nullable=False, index=True)
    remetente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    mensagem = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lida = db.Column(db.Boolean, nullable=False, default=False)

    chamado = db.relationship('ChamadoSuporte', back_populates='mensagens')
    remetente = db.relationship('Usuario', back_populates='mensagens')

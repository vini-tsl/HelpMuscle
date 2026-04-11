# HelpMuscle

Plataforma web para gerencio de treinos personalizados, voltada para alunos e profissionais de educacao fisica.

## Funcionalidades

### Para o Aluno
- Registro, login e recuperacao de senha via codigo por email
- Formulario de perfil (idade, peso, altura, objetivo, nivel de experiencia)
- Geracao automatica de treinos personalizados com base no perfil preenchido
- Dashboard com treinos do dia, progresso e historico
- Execucao de treino com registro de series, peso e reps
- Sugestoes de progressao com base em execucoes anteriores
- Medicao corporal (peso, gordura, cintura, etc.) com grafico de evolucao
- Chat de suporte com profissionais
- Edicao de perfil e alteracao de senha

### Para o Profissional
- Painel com estatisticas gerais (alunos ativos, treinos, progresso)
- Listagem de alunos com filtros e paginacao
- Suporte a chamados abertos com chat em tempo real (polling de 5s)
- Fechar chamados e enviar mensagens

## Stack

| Categoria | Tecnologia |
|---|---|
| Backend | Flask 3, Python 3.12+ |
| Database | SQLite (SQLAlchemy ORM) |
| Templates | Jinja2 |
| Frontend | HTML, CSS, Vanilla JS |
| Rate Limiting | Flask-Limiter |
| CSRF | Flask-WTF |
| Migrations | Flask-Migrate (Alembic) |

## Estrutura do Projeto

```
├── app.py                    # Ponto de entrada, factory pattern
├── models.py                 # Modelos SQLAlchemy (Usuario, Treino, Exercicio, etc.)
├── db.py                     # Instancia SQLAlchemy
├── limiter_ext.py            # Flask-Limiter singleton
├── middleware/auth.py         # Decorators: login_required, profissional_required, admin_required
├── services/treino_engine.py # Motor de geracao automatica de treinos
├── blueprints/
│   ├── auth.py               # Login, registro, recuperacao de senha
│   ├── usuarios.py           # Dashboard, perfil, editar dados
│   ├── treinos.py            # Listagem de treinos, catalogo de exercicios
│   ├── formulario.py         # Formulario de perfil, execucao de treino, historico, medidas
│   ├── profissional.py       # Painel do profissional (stats, alunos)
│   ├── chat.py               # Chat de chamados de suporte
│   ├── suporte.py            # Criacao e gestao de chamados
│   └── admin.py              # Debug endpoints (desenvolvimento)
├── templates/
│   ├── public/               # Homepage, login, registro, esqueci senha
│   ├── user/                 # Painel do aluno (home, treinos, formulario, perfil, chat, historico)
│   └── admin/                # Painel do profissional (alunos, suporte)
├── static/
│   ├── css/                  # CSS organizado por public, user, admin e responsive
│   ├── js/                   # Scripts JS (profissional, treino, esqueceu-senha, login)
│   └── image/                # Imagens e icones
└── instance/users.db         # Banco de dados SQLite (nao versionado)
```

## Instalacao

### 1. Clone o repositorio

```bash
git clone <repo-url>
cd TimbuMuscle
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv HelpMuscle
# Windows:
HelpMuscle\Scripts\activate
# Linux/macOS:
source HelpMuscle/bin/activate
```

### 3. Instale as dependencias

```bash
pip install -r requirements.txt
```

### 4. Configure as variaveis de ambiente

Copie o `.env.example` para `.env` edite conforme necessario:

```env
SECRET_KEY=chave_segura_aqui
DATABASE_URL=sqlite:///instance/users.db
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app
FLASK_ENV=development
DEBUG=True
ADMIN_SECRET=chave_admin_secreta
```

### 5. Inicialize o banco de dados

```bash
flask init-db
```

Popule com dados iniciais (catalogo de exercicios e um profissional padrao):

```bash
python seed_data.py
```

### 6. Rode a aplicacao

```bash
python app.py
```

Acesse em [http://localhost:5000](http://localhost:5000).

## Motor de Treinos

O modulo `services/treino_engine.py` gera treinos automaticamente com base no perfil do aluno:

- **Objetivo**: hipertrofia, emagrecimento, forca, definicao
- **Nivel**: iniciante, intermediario, avancado
- **Dias/semana**: 2 a 6

Para cada dia, seleciona exercicios do `CatalogoExercicio` com series, reps e descanso adequados ao perfil. Recomendo ter pelo menos 20+ exercicios no catalogo para boa variação.

# HelpMuscle

> Plataforma web para gerenciamento de treinos personalizados, acompanhamento de progresso e comunicação entre alunos e profissionais de educação física.

## Sobre o projeto

O **HelpMuscle** é uma aplicação web desenvolvida para auxiliar alunos e profissionais de educação física no gerenciamento de treinos e acompanhamento de evolução.

A plataforma permite que alunos criem seus perfis, recebam treinos personalizados, registrem suas execuções e acompanhem sua evolução ao longo do tempo.

Profissionais possuem uma área administrativa própria para acompanhar alunos e gerenciar chamados de suporte.

## Funcionalidades

### Aluno

* Cadastro e autenticação
* Recuperação de senha por e-mail
* Gerenciamento de perfil
* Definição de objetivo e nível de experiência
* Geração automática de treinos
* Visualização dos treinos
* Registro de séries, repetições e cargas
* Histórico de treinos
* Sugestões de progressão
* Registro de medidas corporais
* Gráficos de evolução
* Chat com profissionais
* Alteração de senha

### Profissional

* Dashboard administrativo
* Estatísticas de alunos
* Listagem de alunos
* Filtros e paginação
* Gerenciamento de chamados
* Comunicação com alunos
* Acompanhamento de progresso

## Motor de geração de treinos

Um dos principais recursos do projeto é o motor responsável pela geração automática de treinos.

A geração considera informações do perfil do aluno, como:

* Objetivo
* Nível de experiência
* Quantidade de dias disponíveis por semana

Exemplos de objetivos:

```text
Hipertrofia
Emagrecimento
Força
Definição
```

O sistema utiliza o catálogo de exercícios para montar os treinos de acordo com o perfil informado.

## Arquitetura

O projeto utiliza uma organização baseada em responsabilidades, separando autenticação, regras de negócio, rotas e serviços.

```text
HelpMuscle/
│
├── blueprints/
│   ├── auth.py
│   ├── usuarios.py
│   ├── treinos.py
│   ├── formulario.py
│   ├── profissional.py
│   ├── chat.py
│   ├── suporte.py
│   └── admin.py
│
├── middleware/
│   └── auth.py
│
├── services/
│   └── treino_engine.py
│
├── templates/
│   ├── public/
│   ├── user/
│   └── admin/
│
├── static/
│   ├── css/
│   ├── js/
│   └── image/
│
├── app.py
├── models.py
├── db.py
├── limiter_ext.py
└── requirements.txt
```

## Tecnologias

| Categoria      | Tecnologia              |
| -------------- | ----------------------- |
| Linguagem      | Python 3.12+            |
| Backend        | Flask 3                 |
| ORM            | SQLAlchemy              |
| Banco de dados | SQLite                  |
| Templates      | Jinja2                  |
| Frontend       | HTML, CSS, JavaScript   |
| Migrations     | Flask-Migrate / Alembic |
| Segurança      | Flask-WTF / CSRF        |
| Rate limiting  | Flask-Limiter           |

## Segurança

O projeto utiliza mecanismos para aumentar a segurança da aplicação, incluindo:

* Proteção CSRF
* Controle de acesso por perfil
* Rate limiting
* Variáveis de ambiente
* Senhas e informações sensíveis fora do código-fonte
* Middleware de autenticação

## Instalação

### 1. Clone o projeto

```bash
git clone https://github.com/vini-tsl/HelpMuscle.git
cd HelpMuscle
```

### 2. Crie o ambiente virtual

```bash
python -m venv venv
```

### 3. Ative o ambiente

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Configure o ambiente

Crie um arquivo `.env` baseado no `.env.example`.

```env
SECRET_KEY=sua_chave
DATABASE_URL=sqlite:///instance/users.db
EMAIL_USER=seu_email
EMAIL_PASSWORD=sua_senha_de_app
FLASK_ENV=development
DEBUG=True
ADMIN_SECRET=sua_chave_admin
```

### 6. Inicialize o banco

```bash
flask init-db
```

### 7. Execute a aplicação

```bash
python app.py
```

A aplicação estará disponível em:

```text
http://localhost:5000
```

## O que aprendi com este projeto

* Desenvolvimento de aplicações Flask
* Organização com Blueprints
* ORM utilizando SQLAlchemy
* Autenticação e autorização
* Migrations com Alembic
* Proteção CSRF
* Rate limiting
* Separação de responsabilidades
* Desenvolvimento de regras de negócio
* Construção de dashboards
* Integração entre frontend e backend

## Status

**Projeto funcional / em evolução**

Novas funcionalidades e melhorias podem ser adicionadas futuramente.

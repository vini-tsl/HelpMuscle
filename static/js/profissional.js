const key = document.body.dataset.key;
let todosAlunos = [];
let paginaAtual = 1;
let totalPaginas = 1;

const dadosMock = {
    estatisticas: {
        total_alunos: 0,
        alunos_ativos: 0,
        alunos_inativos: 0,
        chats_ativos: 0
    },
    alunos: []
};

document.addEventListener('DOMContentLoaded', function() {
    carregarEstatisticas();
    carregarAlunos(paginaAtual);
    document.getElementById('searchInput').addEventListener('input', filtrarPesquisa);
});

async function carregarEstatisticas() {
    try {
        const response = await fetch(`/api/estatisticas/${key}`);
        if (response.ok) {
            const data = await response.json();
            exibirEstatisticas(data);
        }
    } catch (error) {
        exibirEstatisticas(dadosMock.estatisticas);
    }
}

function exibirEstatisticas(data) {
    document.getElementById('statsContainer').innerHTML = `
        <div class="card stat-card">
            <div class="stat-icon icon-primary"><i class="fas fa-users"></i></div>
            <div class="stat-info"><h3>${data.total_alunos || 0}</h3><p>Total de Alunos</p></div>
        </div>
        <div class="card stat-card">
            <div class="stat-icon icon-secondary"><i class="fas fa-dumbbell"></i></div>
            <div class="stat-info"><h3>${data.alunos_ativos || 0}</h3><p>Com Treinos Ativos</p></div>
        </div>
        <div class="card stat-card">
            <div class="stat-icon icon-accent"><i class="fas fa-exclamation-triangle"></i></div>
            <div class="stat-info"><h3>${data.alunos_inativos || 0}</h3><p>Precisam de Acompanhamento</p></div>
        </div>
        <div class="card stat-card">
            <div class="stat-icon icon-primary"><i class="fas fa-comments"></i></div>
            <div class="stat-info"><h3>${data.chats_ativos || 0}</h3><p>Chats Ativos</p></div>
        </div>
    `;
}

async function carregarAlunos(pagina = 1) {
    paginaAtual = pagina;
    try {
        const response = await fetch(`/api/alunos/${key}?pagina=${pagina}`);
        if (!response.ok) {
            if (response.status === 403) {
                alert('Acesso nao autorizado!');
                window.location.href = '/login';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        todosAlunos = data.alunos || [];
        totalPaginas = data.total_paginas || 1;
        renderizarAlunos(todosAlunos);
        renderizarPaginacao();
    } catch (error) {
        todosAlunos = dadosMock.alunos;
        renderizarAlunos(dadosMock.alunos);
    }
}

function renderizarPaginacao() {
    const container = document.getElementById('paginacaoContainer');
    if (totalPaginas <= 1) {
        container.innerHTML = '';
        return;
    }
    container.innerHTML = `
        <div class="paginacao">
            <button class="pag-btn" ${paginaAtual <= 1 ? 'disabled' : ''} onclick="carregarAlunos(${paginaAtual - 1})">
                <i class="fas fa-chevron-left"></i> Anterior
            </button>
            <span class="pag-info">Pagina ${paginaAtual} de ${totalPaginas}</span>
            <button class="pag-btn" ${paginaAtual >= totalPaginas ? 'disabled' : ''} onclick="carregarAlunos(${paginaAtual + 1})">
                Proxima <i class="fas fa-chevron-right"></i>
            </button>
        </div>
    `;
}

function renderizarAlunos(alunos) {
    const tbody = document.getElementById('alunosBody');
    tbody.innerHTML = '';

    if (alunos.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="6" style="text-align:center;padding:40px;color:var(--gray);">
                <i class="fas fa-users" style="font-size:2rem;margin-bottom:10px;display:block;"></i>
                Nenhum aluno encontrado
            </td></tr>`;
        return;
    }

    alunos.forEach(aluno => {
        const statusText = aluno.status === 'Ativo' ? 'Ativo' : 'Precisa de Acompanhamento';
        const statusClass = aluno.status === 'Ativo' ? 'status-active' : 'status-inactive';

        const row = `
            <tr>
                <td><div style="display:flex;align-items:center;">
                    <div class="chat-contact-avatar">${aluno.nome[0]}</div>
                    <div>${aluno.nome}</div>
                </div></td>
                <td>${aluno.treino} - ${aluno.nivel}</td>
                <td>${aluno.ultimo_acesso}</td>
                <td><div class="progress-bar"><div class="progress-fill" style="width:${aluno.progresso}%"></div></div>
                    <small style="color:var(--gray);font-size:0.8rem;display:block;text-align:center;margin-top:5px;">${aluno.progresso}%</small></td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>
                    <button class="action-btn btn-primary" onclick="verAluno(${aluno.id})" title="Ver Detalhes"><i class="fas fa-eye"></i></button>
                    <button class="action-btn" onclick="abrirChat(${aluno.id})" title="Enviar Mensagem"><i class="fas fa-comment"></i></button>
                    ${aluno.status !== 'Ativo' ? `<button class="action-btn btn-warning" onclick="criarTreino(${aluno.id})" title="Criar Treino"><i class="fas fa-plus"></i></button>` : ''}
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

function filtrarAlunos(tipo) {
    if (!todosAlunos || todosAlunos.length === 0) return;
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    let alunosFiltrados;
    if (tipo === 'todos') {
        alunosFiltrados = todosAlunos;
    } else if (tipo === 'ativos') {
        alunosFiltrados = todosAlunos.filter(a => a.status === 'Ativo');
    } else {
        alunosFiltrados = todosAlunos.filter(a => a.status !== 'Ativo');
    }
    renderizarAlunos(alunosFiltrados);
}

function filtrarPesquisa() {
    const termo = document.getElementById('searchInput').value.toLowerCase();
    document.querySelectorAll('#alunosBody tr').forEach(linha => {
        linha.style.display = linha.textContent.toLowerCase().includes(termo) ? '' : 'none';
    });
}

function verAluno(alunoId) { window.location.href = `/aluno/${alunoId}?key=${key}`; }
function abrirChat(alunoId) { window.location.href = `/suporte_profissional/${key}`; }
function criarTreino(alunoId) { window.location.href = `/criar-treino/${alunoId}?key=${key}`; }

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from .models import Usuario, GrOcorrencia,AgendamentoViagem, GrAnexos, CadEntidade, GrPrioridade, CadTpOcorrencia, CadSoftware, CadModulo, CadCarro, Funcionario
from .forms import LoginForm, RegisterForm, OcorrenciaForm, AnexoForm, EntidadeForm, SoftwareForm, ModuloForm, PrioridadeForm, TipoOcorrenciaForm, CarroForm, FuncionarioForm
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from . import db
import requests, random
from random import randint
from flask_paginate import Pagination, get_page_args
from sqlalchemy import and_
import logging

bcrypt = Bcrypt()

main_bp = Blueprint('main', __name__)

# Rotas principais
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user and user.check_senha(form.password.data):
            if not user.autorizado:
                flash('Sua conta ainda não foi autorizada. Aguarde a aprovação do administrador.', 'warning')
            elif not user.ativo:
                flash('Sua conta está inativa. Por favor, entre em contato com o administrador.', 'danger')
            else:
                login_user(user)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('main.index'))
        else:
            flash('Login ou senha incorretos.', 'danger')
    return render_template('login.html', form=form)

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = Usuario(
            nome=form.nome.data,
            email=form.email.data,
            telefone=form.telefone.data,
            perfil='user',
            autorizado=False,
            ativo=True
        )
        user.set_senha(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Aguarde a autorização do administrador.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)


@main_bp.route('/forgot-password')
def forgot_password():
    # Página de recuperação de senha - Implementação futura
    return render_template('forgot_password.html')  # Você pode criar um template para recuperação de senha no futuro.

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sessão.', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/')
@login_required
def index():
    return render_template('main.html')

# Rotas para ocorrências
@main_bp.route('/ocorrencia/nova', methods=['GET', 'POST'])
@login_required
def nova_ocorrencia():
    form = OcorrenciaForm()
    app.logger.info('Form carregado e pronto para validação.')
    
    if form.validate_on_submit():
        app.logger.info('Formulário validado com sucesso.')
        
        try:
            # Gera um número de ocorrência único
            numero_ocorrencia = str(randint(1, 999999)).zfill(6)
            app.logger.info(f'Número da ocorrência gerado: {numero_ocorrencia}')
            
            # Captura os dados do formulário
            ocorrencia = GrOcorrencia(
                numero_ocorrencia=numero_ocorrencia,
                entidade_id = form.entidade_id.data,
                contato=form.contato.data,
                prioridade_id=form.prioridade.data,
                tipo_id=form.tipo.data,
                software_id=form.software.data,
                modulo_id=form.modulo.data,
                descricao=form.descricao.data,
                resolucao=form.resolucao.data,
                situacao = form.situacao.data,
                usuario_id=current_user.id
            )
            
            # Adiciona e comita no banco de dados
            db.session.add(ocorrencia)
            db.session.commit()
            
            app.logger.info('Ocorrência criada e gravada no banco de dados com sucesso.')
            flash('Ocorrência criada com sucesso!', 'success')
            return redirect(url_for('main.meus_atendimentos'))
        
        except Exception as e:
            app.logger.error(f'Erro ao tentar criar ocorrência: {str(e)}')
            flash('Erro ao tentar criar a ocorrência. Verifique os logs para mais detalhes.', 'danger')
    else:
        app.logger.info('Formulário falhou na validação.')
        app.logger.error(f'Erros de validação: {form.errors}')  # Aqui os erros de validação são registrados

    return render_template('ocorrencia_form.html', form=form)



@main_bp.route('/ocorrencia/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_ocorrencia(id):
    # Busca a ocorrência existente no banco de dados
    ocorrencia = GrOcorrencia.query.get_or_404(id)

    # Carregar as opções de tabelas relacionadas
    prioridades = GrPrioridade.query.all()
    tipos = CadTpOcorrencia.query.all()
    softwares = CadSoftware.query.all()
    modulos = CadModulo.query.all()

    # Carrega os dados da ocorrência no formulário para edição
    form = OcorrenciaForm(obj=ocorrencia)
    
    if form.validate_on_submit():
        try:
            # Atualiza os campos da ocorrência existente
            ocorrencia.entidade_id = form.entidade_id.data
            ocorrencia.contato = form.contato.data
            ocorrencia.prioridade_id = form.prioridade.data
            ocorrencia.tipo_id = form.tipo.data
            ocorrencia.software_id = form.software.data
            ocorrencia.modulo_id = form.modulo.data
            ocorrencia.descricao = form.descricao.data
            ocorrencia.resolucao = form.resolucao.data
            ocorrencia.situacao = form.situacao.data

            # Se houver um arquivo anexado, trate o anexo
            if form.anexo.data:
                ocorrencia.anexo = form.anexo.data.filename

            # Salva as mudanças no banco de dados
            db.session.commit()

            # Exibe uma mensagem de sucesso e redireciona
            flash('Ocorrência atualizada com sucesso!', 'success')
            return redirect(url_for('main.meus_atendimentos'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar a ocorrência: {str(e)}', 'danger')

    # Se o método for GET ou o formulário não for válido, renderize o formulário de edição
    return render_template('ocorrencia_form.html', 
                           form=form, 
                           ocorrencia=ocorrencia, 
                           prioridades=prioridades, 
                           tipos=tipos, 
                           softwares=softwares, 
                           modulos=modulos)

@main_bp.route('/ocorrencia/<int:id>/editar-inline', methods=['POST'])
@login_required
def editar_ocorrencia_inline(id):
    # Busca a ocorrência existente no banco de dados
    ocorrencia = GrOcorrencia.query.get_or_404(id)

    try:
        # Coleta os dados da requisição JSON
        data = request.get_json()
        
        # Atualiza os campos da ocorrência com os novos dados enviados via AJAX
        ocorrencia.situacao = data.get('situacao')
        ocorrencia.contato = data.get('contato')
        ocorrencia.descricao = data.get('descricao')
        ocorrencia.resolucao = data.get('resolucao')
        ocorrencia.prioridade_id = data.get('prioridade')
        ocorrencia.tipo_id = data.get('tipo')
        ocorrencia.software_id = data.get('software')
        ocorrencia.modulo_id = data.get('modulo')
        
        # Salva as mudanças no banco de dados
        db.session.commit()

        # Retorna uma resposta de sucesso em JSON
        return jsonify({'success': True}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@main_bp.route('/ocorrencia/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_ocorrencia(id):
    ocorrencia = GrOcorrencia.query.get_or_404(id)
    db.session.delete(ocorrencia)
    db.session.commit()
    flash('Ocorrência excluída com sucesso!', 'success')
    return redirect(url_for('main.meus_atendimentos'))

# Rotas de cadastros com exibição de lista e botão "Novo"
@main_bp.route('/cadastro/entidade', methods=['GET', 'POST'])
@login_required
def listar_entidade():
    entidades = CadEntidade.query.all()
    return render_template('entidade_list.html', entidades=entidades)

@main_bp.route('/cadastro/entidade/nova', methods=['GET', 'POST'])
@login_required
def nova_entidade():
    form = EntidadeForm()
    if form.validate_on_submit():
        entidade = CadEntidade(
            municipio=form.municipio.data,
            cnpj=form.cnpj.data,
            endereco=form.endereco.data,
            telefone=form.telefone.data
        )
        db.session.add(entidade)
        db.session.commit()
        flash('Entidade criada com sucesso!', 'success')
        return redirect(url_for('main.cadastros'))
    return render_template('entidade_form.html', form=form)

@main_bp.route('/entidade/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_entidade(id):
    # Código para excluir a entidade
    return redirect(url_for('main.listar_entidade'))

@main_bp.route('/pesquisa_entidades')
@login_required
def pesquisa_entidades():
    query = request.args.get('q')
    if query:
        entidades = CadEntidade.query.filter(CadEntidade.nome.ilike(f'%{query}%')).all()
        results = [{'id': e.id, 'nome': e.nome} for e in entidades]
        return jsonify(results)
    return jsonify([])

@main_bp.route('/cadastro/entidade/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_entidade(id):
    entidade = CadEntidade.query.get_or_404(id)
    form = EntidadeForm(obj=entidade)

    if form.validate_on_submit():
        # Atualize os dados da entidade
        entidade.municipio = form.municipio.data
        entidade.cnpj = form.cnpj.data
        entidade.endereco = form.endereco.data
        entidade.telefone = form.telefone.data
        db.session.commit()

        flash('Entidade atualizada com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='entidade'))

    return render_template('entidade_form.html', form=form, entidade=entidade)


# Mesma estrutura para módulos, prioridade, tipos de ocorrências, e carro
@main_bp.route('/cadastro/modulo', methods=['GET', 'POST'])
@login_required
def listar_modulo():
    modulos = CadModulo.query.all()
    return render_template('modulo_list.html', modulos=modulos)

@main_bp.route('/cadastro/modulo/nova', methods=['GET', 'POST'])
@login_required
def novo_modulo():
    form = ModuloForm()
    form.software.choices = [(software.id, software.descricao) for software in CadSoftware.query.all()]
    if form.validate_on_submit():
        modulo = CadModulo(
            descricao=form.descricao.data,
            software_id=form.software.data
        )
        db.session.add(modulo)
        db.session.commit()
        flash('Módulo criado com sucesso!', 'success')
        return redirect(url_for('main.listar_modulo'))
    return render_template('modulo_form.html', form=form)

@main_bp.route('/cadastro/modulo/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_modulo(id):
    modulo = CadModulo.query.get_or_404(id)
    form = ModuloForm(obj=modulo)
    form.software.choices = [(software.id, software.descricao) for software in CadSoftware.query.all()]
    if form.validate_on_submit():
        modulo.descricao = form.descricao.data
        modulo.software_id = form.software.data
        db.session.commit()
        flash('Módulo atualizado com sucesso!', 'success')
        return redirect(url_for('main.listar_modulo'))
    return render_template('modulo_form.html', form=form)

# Continuar para as outras abas como prioridade, tipos de ocorrências, e carro

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('main.html')

@main_bp.route('/meus-atendimentos', methods=['GET'])
@login_required
def meus_atendimentos():
    ocorrencias = GrOcorrencia.query.filter_by(usuario_id=current_user.id).all()  # Certifique-se que a consulta está correta
    search_query = request.args.get('search', '').strip()
    query = GrOcorrencia.query.filter_by(usuario_id=current_user.id)
    if search_query:
        query = query.join(CadEntidade).filter(
            (GrOcorrencia.numero_ocorrencia.ilike(f'%{search_query}%')) |
            (CadEntidade.municipio.ilike(f'%{search_query}%')) |
            (GrOcorrencia.data_criacao.ilike(f'%{search_query}%'))
        )
    atendimentos = query.order_by(GrOcorrencia.data_criacao.desc()).limit(5).all()
    return render_template('meus_atendimentos.html', atendimentos=atendimentos)


@main_bp.route('/pesquisa-atendimento', methods=['GET'])
@login_required
def pesquisa_atendimento():
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 15

    # Parâmetros de pesquisa
    search_query = request.args.get('search', '')  # Campo de busca geral (número de ocorrência, município, etc.)
    data_inicio = request.args.get('data_inicio', '')  # Filtro para data de início
    data_fim = request.args.get('data_fim', '')        # Filtro para data de fim
    situacao = request.args.get('situacao', '')        # Filtro por situação

    # Filtros básicos (ocorrências do usuário logado)
    filter_conditions = [GrOcorrencia.usuario_id == current_user.id]

    # Filtro Geral por número de ocorrência, município, prioridade, tipo
    if search_query:
        filter_conditions.append(
            (GrOcorrencia.numero_ocorrencia.ilike(f'%{search_query}%')) |
            (GrOcorrencia.entidade.has(CadEntidade.municipio.ilike(f'%{search_query}%'))) |
            (GrOcorrencia.prioridade.has(GrPrioridade.descricao.ilike(f'%{search_query}%'))) |
            (GrOcorrencia.tipo.has(CadTpOcorrencia.descricao.ilike(f'%{search_query}%')))
        )

    # Filtro por Situação
    if situacao:
        filter_conditions.append(GrOcorrencia.situacao.ilike(f'%{situacao}%'))

    # Filtro por Data de Criação
    if data_inicio and data_fim:
        filter_conditions.append(GrOcorrencia.data_criacao.between(data_inicio, data_fim))
    elif data_inicio:
        filter_conditions.append(GrOcorrencia.data_criacao >= data_inicio)
    elif data_fim:
        filter_conditions.append(GrOcorrencia.data_criacao <= data_fim)

    # Consulta com os filtros aplicados
    atendimentos = GrOcorrencia.query.filter(and_(*filter_conditions)).order_by(GrOcorrencia.data_criacao.desc()).offset(offset).limit(per_page).all()
    total = GrOcorrencia.query.filter(and_(*filter_conditions)).count()

    # Paginação
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    return render_template('pesquisa_atendimento.html', atendimentos=atendimentos, page=page, per_page=per_page, pagination=pagination)

@main_bp.route('/ocorrencia/<int:id>/visualizar', methods=['GET'])
@login_required
def visualizar_ocorrencia(id):
    ocorrencia = GrOcorrencia.query.get_or_404(id)
    
    # Carrega as opções para os campos de seleção (selects)
    prioridades = GrPrioridade.query.all()  # Ajuste de acordo com o seu modelo
    tipos = CadTpOcorrencia.query.all()  # Ajuste de acordo com o seu modelo
    softwares = CadSoftware.query.all()  # Ajuste de acordo com o seu modelo
    modulos = CadModulo.query.all()  # Ajuste de acordo com o seu modelo

    return render_template('visualizar_ocorrencia.html', 
                           ocorrencia=ocorrencia,
                           prioridades=prioridades,
                           tipos=tipos,
                           softwares=softwares,
                           modulos=modulos)



@main_bp.route('/solicitar-ligacao')
@login_required
def solicitar_ligacao():
    return render_template('solicitar_ligacao.html')

@main_bp.route('/cadastros', methods=['GET', 'POST'])
@login_required
def cadastros():
    # Código para carregar e manipular os formulários de cadastro.
    active_tab = request.form.get('active_tab', 'entidade')
    
    # Forms e dados
    entidade_form = EntidadeForm()
    software_form = SoftwareForm()
    modulo_form = ModuloForm()
    modulo_form.software.choices = [(software.id, software.descricao) for software in CadSoftware.query.all()]
    prioridade_form = PrioridadeForm()
    tipo_ocorrencia_form = TipoOcorrenciaForm()
    carro_form = CarroForm()

    # Verificar submissão e salvar dados
    # Código para salvar entidades, software, módulos, etc.

    # Carregar dados para as tabelas
    entidades = CadEntidade.query.order_by(CadEntidade.id.asc()).all()
    softwares = CadSoftware.query.order_by(CadSoftware.id.asc()).all()
    modulos = CadModulo.query.order_by(CadModulo.id.asc()).all()
    prioridades = GrPrioridade.query.order_by(GrPrioridade.id.asc()).all()
    tipos_ocorrencia = CadTpOcorrencia.query.order_by(CadTpOcorrencia.id.asc()).all()
    carros = CadCarro.query.order_by(CadCarro.id.asc()).all()

    return render_template('cadastros.html',
                           entidade_form=entidade_form,
                           software_form=software_form,
                           modulo_form=modulo_form,
                           prioridade_form=prioridade_form,
                           tipo_ocorrencia_form=tipo_ocorrencia_form,
                           carro_form=carro_form,
                           entidades=entidades,
                           softwares=softwares,
                           modulos=modulos,
                           prioridades=prioridades,
                           tipos_ocorrencia=tipos_ocorrencia,
                           carros=carros,
                           active_tab=active_tab)

@main_bp.route('/agendar_viagem', methods=['GET', 'POST'])
@login_required
def agendar_viagem():
    form = AgendamentoViagem()

    # Busca as opções disponíveis para entidades, funcionários e carros
    entidades = CadEntidade.query.all()  # Carregar todas as entidades do banco
    funcionarios = Funcionario.query.all()  # Carregar todos os funcionários
    carros = CadCarro.query.all()  # Carregar todos os carros

    # Preencher as opções nos campos de seleção múltipla
    form.entidades.choices = [(entidade.id, entidade.nome) for entidade in entidades]
    form.funcionarios.choices = [(funcionario.id, funcionario.nome) for funcionario in funcionarios]
    form.carros.choices = [(carro.id, carro.modelo) for carro in carros]

    if form.validate_on_submit():
        try:
            # Lógica para salvar o agendamento da viagem
            viagem = AgendamentoViagem(
                data_viagem=form.data_viagem.data,
                horario_saida=form.horario_saida.data,
                quilometragem=form.quilometragem.data
            )
            
            # Adicionar as entidades vinculadas
            for entidade_id in form.entidades.data:
                entidade = CadEntidade.query.get(entidade_id)
                viagem.entidades.append(entidade)

            # Adicionar os funcionários vinculados
            for funcionario_id in form.funcionarios.data:
                funcionario = Funcionario.query.get(funcionario_id)
                viagem.funcionarios.append(funcionario)

            # Adicionar os carros vinculados
            for carro_id in form.carros.data:
                carro = CadCarro.query.get(carro_id)
                viagem.carros.append(carro)

            db.session.add(viagem)
            db.session.commit()

            flash('Viagem agendada com sucesso!', 'success')
            return redirect(url_for('main.lista_agendamentos'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar o agendamento da viagem: {e}', 'danger')

    return render_template('agendar_viagem.html', form=form)


@main_bp.route('/buscar-entidades')
@login_required
def buscar_entidades():
    query = request.args.get('query', '')

    # Certifique-se de que 'query' seja uma string válida e, em seguida, faça a pesquisa
    if query:
        entidades = CadEntidade.query.filter(
            CadEntidade.municipio.ilike(f"%{query}%")  # Suponha que 'nome' seja o campo correto a ser filtrado
        ).all()

        # Construa a resposta JSON com os dados das entidades
        resultados = [{'id': entidade.id, 'nome': f"{entidade.municipio}"} for entidade in entidades]

        return jsonify({'entidades': resultados})

    return jsonify({'entidades': []})

@main_bp.route('/software/novo', methods=['GET', 'POST'])
@login_required
def novo_software():
    form = SoftwareForm()
    if form.validate_on_submit():
        novo_software = CadSoftware(
            descricao=form.descricao.data
        )
        db.session.add(novo_software)
        db.session.commit()
        flash('Software cadastrado com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='software'))

    return render_template('software_form.html', form=form)

@main_bp.route('/software/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_software(id):
    software = CadSoftware.query.get_or_404(id)
    form = SoftwareForm(obj=software)

    if form.validate_on_submit():
        software.descricao = form.descricao.data
        db.session.commit()
        flash('Software atualizado com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='software'))

    return render_template('software_form.html', form=form)

@main_bp.route('/prioridade/nova', methods=['GET', 'POST'])
@login_required
def nova_prioridade():
    form = PrioridadeForm()

    if form.validate_on_submit():
        nova_prioridade = GrPrioridade(
            descricao=form.descricao.data,
            prazo=form.prazo.data
        )
        db.session.add(nova_prioridade)
        db.session.commit()
        flash('Prioridade cadastrada com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='prioridade'))

    return render_template('prioridade_form.html', form=form)

@main_bp.route('/prioridade/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_prioridade(id):
    prioridade = GrPrioridade.query.get_or_404(id)
    form = PrioridadeForm(obj=prioridade)

    if form.validate_on_submit():
        prioridade.descricao = form.descricao.data
        prioridade.prazo = form.prazo.data
        db.session.commit()
        flash('Prioridade atualizada com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='prioridade'))

    return render_template('prioridade_form.html', form=form, prioridade=prioridade)

@main_bp.route('/tipo_ocorrencia/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo_ocorrencia():
    form = TipoOcorrenciaForm()

    if form.validate_on_submit():
        novo_tipo_ocorrencia = CadTpOcorrencia(
            descricao=form.descricao.data
        )
        db.session.add(novo_tipo_ocorrencia)
        db.session.commit()
        flash('Tipo de ocorrência cadastrado com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='tipo-ocorrencia'))

    return render_template('tipo_ocorrencia_form.html', form=form)

@main_bp.route('/tipo_ocorrencia/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tipo_ocorrencia(id):
    tipo_ocorrencia = CadTpOcorrencia.query.get_or_404(id)
    form = TipoOcorrenciaForm(obj=tipo_ocorrencia)

    if form.validate_on_submit():
        tipo_ocorrencia.descricao = form.descricao.data
        db.session.commit()
        flash('Tipo de ocorrência atualizado com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='tipo-ocorrencia'))

    return render_template('tipo_ocorrencia_form.html', form=form)

@main_bp.route('/carro/novo', methods=['GET', 'POST'])
@login_required
def novo_carro():
    form = CarroForm()

    if form.validate_on_submit():
        novo_carro = CadCarro(
            modelo=form.modelo.data,
            marca=form.marca.data,
            ano=form.ano.data,
            placa=form.placa.data
        )
        db.session.add(novo_carro)
        db.session.commit()
        flash('Carro cadastrado com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='carro'))

    return render_template('carro_form.html', form=form)

@main_bp.route('/carro/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_carro(id):
    carro = CadCarro.query.get_or_404(id)
    form = CarroForm(obj=carro)

    if form.validate_on_submit():
        carro.modelo = form.modelo.data
        carro.marca = form.marca.data
        carro.ano = form.ano.data
        carro.placa = form.placa.data
        db.session.commit()
        flash('Carro atualizado com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='carro'))

    return render_template('carro_form.html', form=form)


import logging

@main_bp.route('/funcionarios/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_funcionario():
    form = FuncionarioForm()

    # Busca os usuários disponíveis para vincular
    usuarios = Usuario.query.all()

    if form.validate_on_submit():
        try:
            funcionario = Funcionario(
                nome=form.nome.data,
                cpf=form.cpf.data,
                rg=form.rg.data,
                cnh=form.cnh.data,
                validade_cnh=form.validade_cnh.data,
                endereco=form.endereco.data,
                setor=form.setor.data,
                email=form.email.data,
                data_admissao=form.data_admissao.data,
                data_demissao=form.data_demissao.data if form.data_demissao.data else None,
                usuario_id=form.usuario_id.data if form.usuario_id.data else None,
                perfil_usuario=form.perfil_usuario.data,
                autorizado=form.autorizado.data,
                ativo=form.ativo.data
            )
            db.session.add(funcionario)
            db.session.commit()
            flash('Funcionário cadastrado com sucesso!', 'success')
            return redirect(url_for('main.listar_funcionarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar funcionário: {e}', 'danger')
    else:
        flash('Erro ao validar o formulário.', 'danger')

    return render_template('cadastrar_funcionario.html', form=form, usuarios=usuarios)


@main_bp.route('/buscar-usuarios', methods=['GET'])
@login_required
def buscar_usuarios():
    query = request.args.get('query')
    
    # Suponha que você tenha uma tabela `Usuario` para buscar os usuários
    usuarios = Usuario.query.filter(Usuario.nome.ilike(f"%{query}%")).all()
    
    # Retorne os resultados no formato necessário (por exemplo, JSON)
    return jsonify({
        'usuarios': [{'id': u.id, 'nome': u.nome} for u in usuarios]
    })

@main_bp.route('/funcionarios', methods=['GET'])
@login_required
def listar_funcionarios():
    funcionarios = Funcionario.query.all()  # Busca todos os funcionários
    return render_template('listar_funcionarios.html', funcionarios=funcionarios)

@main_bp.route('/funcionarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    form = FuncionarioForm(obj=funcionario)

    if form.validate_on_submit():
        try:
            # Atualize os dados do funcionário
            funcionario.nome = form.nome.data
            funcionario.cpf = form.cpf.data
            funcionario.rg = form.rg.data
            funcionario.cnh = form.cnh.data
            funcionario.validade_cnh = form.validade_cnh.data
            funcionario.endereco = form.endereco.data
            funcionario.setor = form.setor.data
            funcionario.email = form.email.data
            funcionario.data_admissao = form.data_admissao.data
            funcionario.data_demissao = form.data_demissao.data
            funcionario.usuario_id = form.usuario_id.data if form.usuario_id.data else None
            funcionario.perfil_usuario = form.perfil_usuario.data
            funcionario.autorizado = form.autorizado.data
            funcionario.ativo = form.ativo.data

            db.session.commit()
            flash('Funcionário atualizado com sucesso!', 'success')
            return redirect(url_for('main.listar_funcionarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar funcionário: {e}', 'danger')

    return render_template('cadastrar_funcionario.html', form=form, usuarios=Usuario.query.all())

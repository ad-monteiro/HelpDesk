from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from .models import Usuario, GrOcorrencia, GrAnexos, CadEntidade, GrPrioridade, CadTpOcorrencia, CadSoftware, CadModulo, TpEntidade, CadCarro, Municipio
from .forms import LoginForm, RegisterForm, OcorrenciaForm, AnexoForm, EntidadeForm, TipoEntidadeForm, SoftwareForm, ModuloForm, PrioridadeForm, TipoOcorrenciaForm, CarroForm
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from . import db
import requests, random
from random import randint
from flask_paginate import Pagination, get_page_args

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
    if form.validate_on_submit():
        numero_ocorrencia = str(randint(1, 999999)).zfill(6)
        ocorrencia = GrOcorrencia(
            numero_ocorrencia=numero_ocorrencia,
            entidade_id=form.entidade.data,
            contato=form.contato.data,
            prioridade_id=form.prioridade.data,
            tipo_id=form.tipo.data,
            software_id=form.software.data,
            modulo_id=form.modulo.data,
            descricao=form.descricao.data,
            resolucao=form.resolucao.data,
            usuario_id=current_user.id
        )
        db.session.add(ocorrencia)
        db.session.commit()
        flash('Ocorrência criada com sucesso!', 'success')
        return redirect(url_for('main.index'))
    return render_template('ocorrencia_form.html', form=form)

@main_bp.route('/ocorrencia/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_ocorrencia(id):
    ocorrencia = GrOcorrencia.query.get_or_404(id)
    form = OcorrenciaForm(obj=ocorrencia)
    if form.validate_on_submit():
        ocorrencia.entidade_id = form.entidade.data
        ocorrencia.contato = form.contato.data
        ocorrencia.prioridade_id = form.prioridade.data
        ocorrencia.tipo_id = form.tipo.data
        ocorrencia.software_id = form.software.data
        ocorrencia.modulo_id = form.modulo.data
        ocorrencia.descricao = form.descricao.data
        ocorrencia.resolucao = form.resolucao.data
        db.session.commit()
        flash('Ocorrência atualizada com sucesso!', 'success')
        return redirect(url_for('main.meus_atendimentos'))
    return render_template('ocorrencia_form.html', form=form)

@main_bp.route('/ocorrencia/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_ocorrencia(id):
    ocorrencia = GrOcorrencia.query.get_or_404(id)
    db.session.delete(ocorrencia)
    db.session.commit()
    flash('Ocorrência excluída com sucesso!', 'success')
    return redirect(url_for('main.index'))

# Rotas de cadastros com exibição de lista e botão "Novo"
@main_bp.route('/cadastro/entidade', methods=['GET'])
@login_required
def listar_entidade():
    entidades = CadEntidade.query.order_by(CadEntidade.id.asc()).all()  # Ordena por ID crescente
    return render_template('entidade_list.html', entidades=entidades)

@main_bp.route('/cadastro/entidade/nova', methods=['GET', 'POST'])
@login_required
def nova_entidade():
    form = EntidadeForm()
    form.tipo_entidade.choices = [(tipo.id, tipo.descricao) for tipo in TpEntidade.query.all()]
    if form.validate_on_submit():
        entidade = CadEntidade(
            municipio=form.municipio.data,
            tipo_entidade_id=form.tipo_entidade.data,
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


@main_bp.route('/cadastro/entidade/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_entidade(id):
    # Carregar a entidade existente pelo ID ou retornar erro 404
    entidade = CadEntidade.query.get_or_404(id)

    # Inicializar o formulário com os dados da entidade existente
    form = EntidadeForm(obj=entidade)

    # Preencher as opções do campo tipo_entidade (para dropdown)
    form.tipo_entidade.choices = [(tipo.id, tipo.descricao) for tipo in TpEntidade.query.all()]

    if form.validate_on_submit():
        # Atualizar os campos da entidade com os dados do formulário
        entidade.municipio = form.municipio.data
        entidade.tipo_entidade_id = form.tipo_entidade.data
        entidade.cnpj = form.cnpj.data
        entidade.endereco = form.endereco.data
        entidade.telefone = form.telefone.data
        
        # Comitar as mudanças no banco de dados
        db.session.commit()

        # Exibir uma mensagem de sucesso
        flash('Entidade atualizada com sucesso!', 'success')

        # Redirecionar para a página de cadastros
        return redirect(url_for('main.cadastros', _anchor='entidade'))

    # Renderizar o formulário de edição com os dados da entidade
    return render_template('entidade_form.html', form=form)


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
    search_query = request.args.get('search', '')
    filter_conditions = [GrOcorrencia.usuario_id == current_user.id]
    
    if search_query:
        filter_conditions.append(
            (GrOcorrencia.numero_ocorrencia.ilike(f'%{search_query}%')) |
            (GrOcorrencia.entidade.has(CadEntidade.municipio.ilike(f'%{search_query}%'))) |
            (GrOcorrencia.prioridade.has(GrPrioridade.descricao.ilike(f'%{search_query}%'))) |
            (GrOcorrencia.tipo.has(CadTpOcorrencia.descricao.ilike(f'%{search_query}%')))
        )

    atendimentos = GrOcorrencia.query.filter(*filter_conditions).order_by(GrOcorrencia.data_criacao.desc()).offset(offset).limit(per_page).all()
    total = GrOcorrencia.query.filter(*filter_conditions).count()
    
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    return render_template('pesquisa_atendimento.html', atendimentos=atendimentos, page=page, per_page=per_page, pagination=pagination)

@main_bp.route('/ocorrencia/<int:id>/visualizar', methods=['GET'])
@login_required
def visualizar_ocorrencia(id):
    ocorrencia = GrOcorrencia.query.get_or_404(id)  # Busca a ocorrência ou retorna 404 se não existir
    return render_template('visualizar_ocorrencia.html', ocorrencia=ocorrencia)


@main_bp.route('/solicitar-ligacao')
@login_required
def solicitar_ligacao():
    return render_template('solicitar_ligacao.html')

@main_bp.route('/cadastros', methods=['GET', 'POST'])
@login_required
def cadastros():
    # Código para carregar e manipular os formulários de cadastro.
    active_tab = request.form.get('active_tab', 'tipo-entidade')
    
    # Forms e dados
    tipo_entidade_form = TipoEntidadeForm()
    entidade_form = EntidadeForm()
    entidade_form.tipo_entidade.choices = [(tipo.id, tipo.descricao) for tipo in TpEntidade.query.all()]
    software_form = SoftwareForm()
    modulo_form = ModuloForm()
    modulo_form.software.choices = [(software.id, software.descricao) for software in CadSoftware.query.all()]
    prioridade_form = PrioridadeForm()
    tipo_ocorrencia_form = TipoOcorrenciaForm()
    carro_form = CarroForm()

    # Verificar submissão e salvar dados
    # Código para salvar entidades, software, módulos, etc.

    # Carregar dados para as tabelas
    tipos_entidade = TpEntidade.query.all()
    entidades = CadEntidade.query.all()
    softwares = CadSoftware.query.all()
    modulos = CadModulo.query.all()
    prioridades = GrPrioridade.query.all()
    tipos_ocorrencia = CadTpOcorrencia.query.all()
    carros = CadCarro.query.all()

    return render_template('cadastros.html',
                           tipo_entidade_form=tipo_entidade_form,
                           entidade_form=entidade_form,
                           software_form=software_form,
                           modulo_form=modulo_form,
                           prioridade_form=prioridade_form,
                           tipo_ocorrencia_form=tipo_ocorrencia_form,
                           carro_form=carro_form,
                           tipos_entidade=tipos_entidade,
                           entidades=entidades,
                           softwares=softwares,
                           modulos=modulos,
                           prioridades=prioridades,
                           tipos_ocorrencia=tipos_ocorrencia,
                           carros=carros,
                           active_tab=active_tab)

@main_bp.route('/agendar-viagem')
@login_required
def agendar_viagem():
    return render_template('agendar_viagem.html')

@main_bp.route('/cadastro/tipo-entidade/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo_entidade():
    form = TipoEntidadeForm()
    if form.validate_on_submit():
        tipo_entidade = TpEntidade(descricao=form.descricao.data)
        db.session.add(tipo_entidade)
        db.session.commit()
        flash('Tipo de entidade criado com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='tipo-entidade'))
    return render_template('tipo_entidade_form.html', form=form)

@main_bp.route('/tipo-entidade/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tipo_entidade(id):
    tipo_entidade = TpEntidade.query.get_or_404(id)
    form = TipoEntidadeForm(obj=tipo_entidade)

    if form.validate_on_submit():
        tipo_entidade.descricao = form.descricao.data
        db.session.commit()
        flash('Tipo de entidade atualizado com sucesso!', 'success')
        return redirect(url_for('main.cadastros', active_tab='tipo-entidade'))

    return render_template('tipo_entidade_form.html', form=form, tipo_entidade=tipo_entidade)

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


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

bcrypt = Bcrypt()

main_bp = Blueprint('main', __name__)

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

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sessão.', 'info')
    return redirect(url_for('main.login'))

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
        user.set_senha(form.password.data)  # Usando o método do modelo para criar o hash da senha
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Aguarde a autorização do administrador.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)


@main_bp.route('/')
@login_required
def index():
    ocorrencias = GrOcorrencia.query.all()  # Carrega todas as ocorrências do banco de dados
    return render_template('index.html', ocorrencias=ocorrencias)  # Passa as ocorrências para o template

@main_bp.route('/ocorrencia/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_ocorrencia(id):
    ocorrencia = GrOcorrencia.query.get_or_404(id)
    form = OcorrenciaForm(obj=ocorrencia)
    
    if form.validate_on_submit():
        form.populate_obj(ocorrencia)  # Preenche a ocorrência com os dados do formulário
        
        try:
            db.session.commit()
            flash('Ocorrência atualizada com sucesso!', 'success')
            return redirect(url_for('main.meus_atendimentos'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Erro ao atualizar ocorrência: {e}')
            flash('Erro ao atualizar ocorrência. Verifique os dados e tente novamente.', 'danger')
    
    return render_template('ocorrencia_form.html', form=form)


@main_bp.route('/ocorrencia/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_ocorrencia(id):
    ocorrencia = GrOcorrencia.query.get_or_404(id)
    db.session.delete(ocorrencia)
    db.session.commit()
    flash('Ocorrência excluída com sucesso!', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/forgot-password')
def forgot_password():
    # Implementação futura
    return "Página de recuperação de senha - Em construção"

@main_bp.route('/admin/gerenciar-usuarios')
@login_required
def gerenciar_usuarios():
    if current_user.perfil != 'admin':
        flash('Acesso negado: você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))

    usuarios = Usuario.query.all()
    return render_template('gerenciar_usuarios.html', usuarios=usuarios)

@main_bp.route('/admin/toggle-ativo/<int:user_id>', methods=['POST'])
@login_required
def toggle_ativo(user_id):
    if current_user.perfil != 'admin':
        flash('Acesso negado: você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))

    usuario = Usuario.query.get_or_404(user_id)
    usuario.ativo = not usuario.ativo
    db.session.commit()
    flash(f'Usuário {"ativado" if usuario.ativo else "desativado"} com sucesso.', 'success')
    return redirect(url_for('main.gerenciar_usuarios'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')

@main_bp.route('/meus-atendimentos', methods=['GET'])
@login_required
def meus_atendimentos():
    atendimentos = GrOcorrencia.query.filter_by(usuario_id=current_user.id).all()
    return render_template('meus_atendimentos.html', atendimentos=atendimentos)

@main_bp.route('/solicitar-ligacao')
@login_required
def solicitar_ligacao():
    return render_template('solicitar_ligacao.html')

@main_bp.route('/agendar-viagem')
@login_required
def agendar_viagem():
    return render_template('agendar_viagem.html')

@main_bp.route('/cadastros', methods=['GET', 'POST'])
@login_required
def cadastros():
    active_tab = request.form.get('active_tab', 'tipo-entidade')
    
    # Forms
    tipo_entidade_form = TipoEntidadeForm()
    entidade_form = EntidadeForm()
    entidade_form.tipo_entidade.choices = [(tipo.id, tipo.descricao) for tipo in TpEntidade.query.all()]
    
    software_form = SoftwareForm()
    modulo_form = ModuloForm()
    modulo_form.software.choices = [(software.id, software.descricao) for software in CadSoftware.query.all()]
    prioridade_form = PrioridadeForm()
    tipo_ocorrencia_form = TipoOcorrenciaForm()
    carro_form = CarroForm()
    
    # Verificar se um formulário específico foi submetido
    if tipo_entidade_form.validate_on_submit():
        # Código para salvar Tipo Entidade
        tipo_entidade = TpEntidade(descricao=tipo_entidade_form.descricao.data)
        db.session.add(tipo_entidade)
        db.session.commit()
        active_tab = 'tipo-entidade'
        flash('Tipo de entidade cadastrado com sucesso!', 'success')
        
    elif entidade_form.validate_on_submit():
        # Código para salvar Entidade
        entidade = CadEntidade(
            municipio=entidade_form.municipio.data,
            tipo_entidade_id=entidade_form.tipo_entidade.data,
            cnpj=entidade_form.cnpj.data,
            endereco=entidade_form.endereco.data,
            telefone=entidade_form.telefone.data
        )
        db.session.add(entidade)
        db.session.commit()
        active_tab = 'entidade'
        flash('Entidade cadastrada com sucesso!', 'success')
        
    elif software_form.validate_on_submit():
        # Código para salvar Software
        software = CadSoftware(descricao=software_form.descricao.data)
        db.session.add(software)
        db.session.commit()
        active_tab = 'software'
        flash('Software cadastrado com sucesso!', 'success')
        
    elif modulo_form.validate_on_submit():
        # Código para salvar Módulo
        modulo = CadModulo(
            descricao=modulo_form.descricao.data,
            software_id=modulo_form.software.data
        )
        db.session.add(modulo)
        db.session.commit()
        active_tab = 'modulo'
        flash('Módulo cadastrado com sucesso!', 'success')
        
    elif prioridade_form.validate_on_submit():
        # Código para salvar Prioridade
        prioridade = GrPrioridade(
            descricao=prioridade_form.descricao.data,
            prazo=prioridade_form.prazo.data
        )
        db.session.add(prioridade)
        db.session.commit()
        active_tab = 'prioridade'
        flash('Prioridade cadastrada com sucesso!', 'success')
        
    elif tipo_ocorrencia_form.validate_on_submit():
        # Código para salvar Tipo Ocorrência
        tipo_ocorrencia = CadTpOcorrencia(descricao=tipo_ocorrencia_form.descricao.data)
        db.session.add(tipo_ocorrencia)
        db.session.commit()
        active_tab = 'tipo-ocorrencia'
        flash('Tipo de ocorrência cadastrado com sucesso!', 'success')
        
    elif carro_form.validate_on_submit():
        # Código para salvar Carro
        carro = CadCarro(
            nome=carro_form.nome.data,
            placa=carro_form.placa.data
        )
        db.session.add(carro)
        db.session.commit()
        active_tab = 'carro'
        flash('Carro cadastrado com sucesso!', 'success')
    
    # Carregar dados para os selects e tabelas
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
# Rotas para cada cadastro

@main_bp.route('/cadastro/entidade', methods=['POST'])
@login_required
def cadastrar_entidade():
    form = EntidadeForm()
    if form.validate_on_submit():
        app.logger.info(f'Recebido formulário: {form.data}')
        nova_entidade = CadEntidade(
            municipio=form.municipio.data,
            tipo_entidade_id=form.tipo_entidade.data,
            cnpj=form.cnpj.data,
            endereco=form.endereco.data,
            telefone=form.telefone.data
        )
        try:
            db.session.add(nova_entidade)
            db.session.commit()
            app.logger.info(f'Entidade inserida: {nova_entidade}')
            flash('Entidade cadastrada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Erro ao inserir entidade: {e}')
            flash('Erro ao cadastrar entidade. Verifique os dados e tente novamente.', 'danger')
    else:
        # Log detalhado dos erros de validação
        for field, errors in form.errors.items():
            for error in errors:
                app.logger.warning(f"Erro no campo {field}: {error}")
        flash('Erro ao cadastrar entidade. Verifique os dados e tente novamente.', 'danger')
    
    return redirect(url_for('main.cadastros', active_tab='entidade'))

@main_bp.route('/cadastro/tipo_entidade', methods=['POST'])
@login_required
def cadastrar_tipo_entidade():
    active_tab = request.form.get('active_tab', 'tipo-entidade')
    form = TipoEntidadeForm()
    if form.validate_on_submit():
        novo_tipo = TpEntidade(
            descricao=form.descricao.data
        )
        db.session.add(novo_tipo)
        db.session.commit()
        flash('Tipo de Entidade cadastrado com sucesso!', 'success')
    return redirect(url_for('main.cadastros', tab='tipo-entidade'))

@main_bp.route('/cadastro/software', methods=['POST'])
@login_required
def cadastrar_software():
    active_tab = request.form.get('active_tab', 'software')
    form = SoftwareForm()
    if form.validate_on_submit():
        novo_software = CadSoftware(
            descricao=form.descricao.data
        )
        db.session.add(novo_software)
        db.session.commit()
        flash('Software cadastrado com sucesso!', 'success')
    return redirect(url_for('main.cadastros'))

@main_bp.route('/cadastro/modulo', methods=['POST'])
@login_required
def cadastrar_modulo():
    active_tab = request.form.get('active_tab', 'modulo')
    form = ModuloForm()
    if form.validate_on_submit():
        novo_modulo = CadModulo(
            software_id=form.software.data,
            descricao=form.descricao.data
        )
        db.session.add(novo_modulo)
        db.session.commit()
        flash('Módulo cadastrado com sucesso!', 'success')
    return redirect(url_for('main.cadastros'))

@main_bp.route('/cadastro/prioridade', methods=['POST'])
@login_required
def cadastrar_prioridade():
    active_tab = request.form.get('active_tab', 'prioridade')
    form = PrioridadeForm()
    if form.validate_on_submit():
        nova_prioridade = GrPrioridade(
            descricao=form.descricao.data,
            prazo=form.prazo.data
        )
        db.session.add(nova_prioridade)
        db.session.commit()
        flash('Prioridade cadastrada com sucesso!', 'success')
    return redirect(url_for('main.cadastros'))

@main_bp.route('/cadastro/tipo_ocorrencia', methods=['POST'])
@login_required
def cadastrar_tipo_ocorrencia():
    active_tab = request.form.get('active_tab', 'tipo_ocorrencia')
    form = TipoOcorrenciaForm()
    if form.validate_on_submit():
        novo_tipo_ocorrencia = CadTpOcorrencia(
            descricao=form.descricao.data
        )
        db.session.add(novo_tipo_ocorrencia)
        db.session.commit()
        flash('Tipo de Ocorrência cadastrado com sucesso!', 'success')
    return redirect(url_for('main.cadastros'))

@main_bp.route('/cadastro/carro', methods=['POST'])
@login_required
def cadastrar_carro():
    active_tab = request.form.get('active_tab', 'carro')
    form = CarroForm()
    if form.validate_on_submit():
        novo_carro = CadCarro(
            modelo=form.modelo.data,
            placa=form.placa.data,
            ano=form.ano.data,
            marca=form.marca.data
        )
        db.session.add(novo_carro)
        db.session.commit()
        flash('Carro cadastrado com sucesso!', 'success')
    return redirect(url_for('main.cadastros'))

@main_bp.route('/buscar_municipio', methods=['GET'])
@login_required
def buscar_municipio():
    query = request.args.get('query', '')
    if query:
        municipios = Municipio.query.filter(
            (Municipio.codigo_ibge.ilike(f'%{query}%')) |
            (Municipio.nome.ilike(f'%{query}%'))
        ).all()
    else:
        municipios = Municipio.query.limit(10).all()  # Limita os resultados se não houver query

    results = [{'codigo_ibge': m.codigo_ibge, 'nome': m.nome} for m in municipios]
    return jsonify(municipios=results)


import random
import os
from werkzeug.utils import secure_filename
from datetime import datetime

import random

@main_bp.route('/ocorrencia/nova', methods=['GET', 'POST'])
@login_required
def nova_ocorrencia():
    form = OcorrenciaForm()
    if form.validate_on_submit():
        # Gerar número da ocorrência com 6 dígitos
        numero_ocorrencia = str(randint(1, 999999)).zfill(6)
        
        # Criando nova ocorrência
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
            usuario_id=current_user.id  # Certifique-se de que o ID do usuário esteja sendo atribuído
        )
        db.session.add(ocorrencia)
        db.session.commit()

        # Gerenciamento de anexo (mantido conforme seu código atual)
        if form.anexo.data:
            filename = secure_filename(form.anexo.data.filename)
            filepath = os.path.join('caminho_para_armazenar_arquivos', filename)
            form.anexo.data.save(filepath)
            
            anexo = GrAnexos(
                ocorrencia_id=ocorrencia.id,
                arquivo=open(filepath, 'rb').read(),
                nome_arquivo=filename,
                tipo_arquivo=form.anexo.data.mimetype,
                data_upload=datetime.utcnow()
            )
            db.session.add(anexo)
            db.session.commit()

        flash('Ocorrência criada com sucesso!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('ocorrencia_form.html', form=form)

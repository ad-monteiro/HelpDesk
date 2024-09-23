from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, FileField, PasswordField, EmailField, ValidationError, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from .models import Usuario, CadEntidade, GrPrioridade, CadTpOcorrencia, CadSoftware, CadModulo

class OcorrenciaForm(FlaskForm):
    numero_ocorrencia = StringField('Número da Ocorrência', render_kw={'readonly': True})  # Campo desabilitado
    entidade_id = HiddenField('Entidade ID', validators=[DataRequired()])
    contato = TextAreaField('Contato', validators=[DataRequired()])
    prioridade = SelectField('Prioridade', choices=[], coerce=int, validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[], coerce=int, validators=[DataRequired()])
    software = SelectField('Software', choices=[], coerce=int, validators=[DataRequired()])
    modulo = SelectField('Módulo', choices=[], coerce=int, validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    resolucao = TextAreaField('Resolução')
    anexo = FileField('Anexar Arquivo')  # Campo para anexar arquivo
    situacao = SelectField('Situação', choices=[
        ('aberto', 'Aberto'),
        ('analise', 'Em análise'),
        ('aguardando', 'Aguardando Programação'),
        ('finalizado', 'Finalizado')
    ], validators=[DataRequired()])
    submit = SubmitField('Salvar Alterações')

    def __init__(self, *args, **kwargs):
        super(OcorrenciaForm, self).__init__(*args, **kwargs)
        # As opções para os campos de prioridade, tipo, software e módulo continuam sendo carregadas
        self.prioridade.choices = [(p.id, p.descricao) for p in GrPrioridade.query.all()]
        self.tipo.choices = [(t.id, t.descricao) for t in CadTpOcorrencia.query.all()]
        self.software.choices = [(s.id, s.descricao) for s in CadSoftware.query.all()]
        self.modulo.choices = [(m.id, m.descricao) for m in CadModulo.query.all()]

class AnexoForm(FlaskForm):
    arquivo = FileField('Arquivo', validators=[DataRequired()])
    submit = SubmitField('Enviar Anexo')

class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirme a Senha', validators=[DataRequired(), EqualTo('password')])
    telefone = StringField('Telefone', validators=[DataRequired()])
    submit = SubmitField('Cadastrar-se')

    def validate_email(self, email):
        user = Usuario.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('E-mail já cadastrado. Use outro e-mail.')

class EntidadeForm(FlaskForm):
    id = HiddenField()
    municipio = StringField('Município', validators=[DataRequired()])
    cnpj = StringField('CNPJ', validators=[DataRequired()])
    endereco = StringField('Endereço', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])


class TipoEntidadeForm(FlaskForm):
    descricao = StringField('Descrição', validators=[DataRequired()])
    abreviacao = StringField('Abreviação', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class SoftwareForm(FlaskForm):
    descricao = StringField('Descrição', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class ModuloForm(FlaskForm):
    software = SelectField('Software', choices=[], coerce=int, validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class PrioridadeForm(FlaskForm):
    descricao = StringField('Descrição', validators=[DataRequired()])
    prazo = StringField('Prazo', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class TipoOcorrenciaForm(FlaskForm):
    descricao = StringField('Descrição', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class CarroForm(FlaskForm):
    modelo = StringField('Modelo', validators=[DataRequired()])
    placa = StringField('Placa', validators=[DataRequired()])
    ano = StringField('Ano', validators=[DataRequired()])
    marca = StringField('Marca', validators=[DataRequired()])
    submit = SubmitField('Salvar')
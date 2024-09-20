from . import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    perfil = db.Column(db.String(20), nullable=False)
    autorizado = db.Column(db.Boolean, default=False, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def set_senha(self, senha):
        self.senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

    def check_senha(self, senha):
        return bcrypt.check_password_hash(self.senha_hash, senha)

class CadSuporte(db.Model):
    __tablename__ = 'cad_suporte'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    endereco = db.Column(db.String(255))
    cnh = db.Column(db.String(50))
    telefone = db.Column(db.String(20))
    cpf = db.Column(db.String(14), unique=True)
    setor = db.Column(db.String(100))

class TpEntidade(db.Model):
    __tablename__ = 'tp_entidade'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    abreviacao = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        return f'<TpEntidade {self.descricao}>'
    
class CadEntidade(db.Model):
    __tablename__ = 'cad_entidade'
    id = db.Column(db.Integer, primary_key=True)
    municipio = db.Column(db.String(255))
    cnpj = db.Column(db.String(18), unique=True)
    endereco = db.Column(db.String(255))
    telefone = db.Column(db.String(20))
    tipo_entidade_id = db.Column(db.Integer, db.ForeignKey('tp_entidade.id'), nullable=True)
    tipo_entidade = db.relationship('TpEntidade')

class GrPrioridade(db.Model):
    __tablename__ = 'gr_prioridade'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(255), nullable=False)
    prazo = db.Column(db.Integer)

class CadTpOcorrencia(db.Model):
    __tablename__ = 'cad_tpocorrencia'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(255), nullable=False)

class CadSoftware(db.Model):
    __tablename__ = 'cad_software'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(255), nullable=False)

class CadModulo(db.Model):
    __tablename__ = 'cad_modulo'
    id = db.Column(db.Integer, primary_key=True)
    software_id = db.Column(db.Integer, db.ForeignKey('cad_software.id'), nullable=False)
    software = db.relationship('CadSoftware')
    descricao = db.Column(db.String(255), nullable=False)

class GrOcorrencia(db.Model):
    __tablename__ = 'gr_ocorrencia'
    id = db.Column(db.Integer, primary_key=True)
    numero_ocorrencia = db.Column(db.String(6), unique=True, nullable=False)
    entidade_id = db.Column(db.Integer, db.ForeignKey('cad_entidade.id'))
    entidade = db.relationship('CadEntidade', backref='ocorrencias')
    contato = db.Column(db.String(255), nullable=False)
    prioridade_id = db.Column(db.Integer, db.ForeignKey('gr_prioridade.id'), nullable=False)
    prioridade = db.relationship('GrPrioridade', backref='ocorrencias')
    tipo_id = db.Column(db.Integer, db.ForeignKey('cad_tpocorrencia.id'), nullable=False)  # Ajuste aqui para refletir o relacionamento correto
    tipo = db.relationship('CadTpOcorrencia', backref='ocorrencias')  # Adicione esta linha
    software_id = db.Column(db.Integer, db.ForeignKey('cad_software.id'), nullable=False)
    software = db.relationship('CadSoftware', backref='ocorrencias')
    modulo_id = db.Column(db.Integer, db.ForeignKey('cad_modulo.id'), nullable=False)
    modulo = db.relationship('CadModulo', backref='ocorrencias')
    descricao = db.Column(db.Text, nullable=False)
    resolucao = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # Adicione essa linha
    usuario = db.relationship('Usuario', backref='ocorrencias')

class CadCarro(db.Model):
    __tablename__ = 'cad_carro'
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(255), nullable=False)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    ano = db.Column(db.String(4), unique=True, nullable=False)
    marca = db.Column(db.String(20), nullable=False)

class GrRelViagemSup(db.Model):
    __tablename__ = 'gr_rel_viagemsup'
    id = db.Column(db.Integer, primary_key=True)
    suporte_id = db.Column(db.Integer, db.ForeignKey('cad_suporte.id'), nullable=False)
    suporte = db.relationship('CadSuporte')
    ocorrencia = db.Column(db.Text)

class GrViagem(db.Model):
    __tablename__ = 'gr_viagem'
    id = db.Column(db.Integer, primary_key=True)
    entidade_id = db.Column(db.Integer, db.ForeignKey('cad_entidade.id'), nullable=True)
    entidade = db.relationship('CadEntidade')
    carro_id = db.Column(db.Integer, db.ForeignKey('cad_carro.id'), nullable=True)
    carro = db.relationship('CadCarro')
    data = db.Column(db.Date)
    horario = db.Column(db.Time)
    suporte_id = db.Column(db.Integer, db.ForeignKey('cad_suporte.id'), nullable=True)
    suporte = db.relationship('CadSuporte')
    ocorrencia_id = db.Column(db.Integer, db.ForeignKey('gr_rel_viagemsup.id'), nullable=False)
    ocorrencia = db.relationship('GrRelViagemSup')

class GrAnexos(db.Model):
    __tablename__ = 'gr_anexos'
    id = db.Column(db.Integer, primary_key=True)
    ocorrencia_id = db.Column(db.Integer, db.ForeignKey('gr_ocorrencia.id'), nullable=False)
    ocorrencia = db.relationship('GrOcorrencia')
    arquivo = db.Column(db.LargeBinary, nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    tipo_arquivo = db.Column(db.String(100), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)

class Municipio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo_ibge = db.Column(db.String(10), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    ultimo_censo = db.Column(db.String(100))  # Pode ser outro tipo, dependendo dos dados
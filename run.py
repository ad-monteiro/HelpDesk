from app import create_app, db
import logging
from logging.handlers import RotatingFileHandler

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

@app.cli.command('create-db')
def create_db():
    db.create_all()
    print("Banco de dados criado com sucesso!")

if not app.debug:
    # Configurar o arquivo de log
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Aplicativo inicializado')
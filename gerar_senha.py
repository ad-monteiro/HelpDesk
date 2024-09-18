from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
hashed_senha = bcrypt.generate_password_hash('Satelliteahm20').decode('utf-8')
print(hashed_senha)

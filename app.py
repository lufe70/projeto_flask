from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Inicialização do Flask e configuração do banco de dados
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///produtos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelo básico - apenas com campos essenciais
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text, nullable=True)  # Novo campo
    
    def __repr__(self):
        return f'<Produto {self.nome}>'

# Rota principal - lista produtos
@app.route('/')
def listar_produtos():
    produtos = Produto.query.all()
    return render_template('listar.html', produtos=produtos)

# Rota para adicionar produto
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        descricao = request.form.get('descricao', '')  # Pega descrição com valor padrão vazio
        
        novo_produto = Produto(nome=nome, preco=preco, descricao=descricao)
        db.session.add(novo_produto)
        db.session.commit()
        
        return redirect(url_for('listar_produtos'))
    
    return render_template('adicionar.html')

# Criar tabelas e inserir dados de exemplo
with app.app_context():
    db.create_all()
    
    # Adicionar produtos de exemplo se o banco estiver vazio
    # if Produto.query.count() == 0:
    #     produtos_exemplo = [
    #         Produto(nome='Camiseta', preco=49.90),
    #         Produto(nome='Calça Jeans', preco=99.90)
    #     ]
    #     db.session.add_all(produtos_exemplo)
    #     db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
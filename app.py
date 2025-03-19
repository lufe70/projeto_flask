from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Inicialização do Flask e configuração do banco de dados
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///produtos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'chave-secreta-para-flash-messages'  # Necessário para flash messages
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelo básico com campo de descrição
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    
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
        # Extrair os dados do formulário
        nome = request.form.get('nome', '').strip()
        preco_str = request.form.get('preco', '').strip()
        descricao = request.form.get('descricao', '').strip()
        
        # Validação de formulário
        errors = []
        
        if not nome:
            errors.append('O nome do produto é obrigatório.')
        elif len(nome) < 3:
            errors.append('O nome do produto deve ter pelo menos 3 caracteres.')
        elif len(nome) > 100:
            errors.append('O nome do produto não pode ter mais de 100 caracteres.')
        
        try:
            if not preco_str:
                errors.append('O preço do produto é obrigatório.')
            else:
                preco = float(preco_str)
                if preco < 0:
                    errors.append('O preço não pode ser negativo.')
        except ValueError:
            errors.append('O preço deve ser um número válido.')
            preco = 0
        
        if len(descricao) > 500:
            errors.append('A descrição não pode ter mais de 500 caracteres.')
        
        # Se houver erros, mostre-os e volte ao formulário
        if errors:
            for error in errors:
                flash(error, 'danger')
            # Retorna ao formulário com os dados preenchidos para correção
            return render_template('adicionar.html', produto={'nome': nome, 'preco': preco_str, 'descricao': descricao})
        
        # Se não houver erros, prossegue com a adição ao banco
        novo_produto = Produto(nome=nome, preco=preco, descricao=descricao)
        db.session.add(novo_produto)
        db.session.commit()
        
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
    
    return render_template('adicionar.html')

# Nova rota para editar produto
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    
    if request.method == 'POST':
        # Extrair os dados do formulário
        nome = request.form.get('nome', '').strip()
        preco_str = request.form.get('preco', '').strip()
        descricao = request.form.get('descricao', '').strip()
        
        # Validação de formulário
        errors = []
        
        if not nome:
            errors.append('O nome do produto é obrigatório.')
        elif len(nome) < 3:
            errors.append('O nome do produto deve ter pelo menos 3 caracteres.')
        elif len(nome) > 100:
            errors.append('O nome do produto não pode ter mais de 100 caracteres.')
        
        try:
            if not preco_str:
                errors.append('O preço do produto é obrigatório.')
            else:
                preco = float(preco_str)
                if preco < 0:
                    errors.append('O preço não pode ser negativo.')
        except ValueError:
            errors.append('O preço deve ser um número válido.')
            preco = 0
        
        if len(descricao) > 500:
            errors.append('A descrição não pode ter mais de 500 caracteres.')
        
        # Se houver erros, mostre-os e volte ao formulário
        if errors:
            for error in errors:
                flash(error, 'danger')
            # Cria um dicionário com os dados atuais para preencher o formulário
            produto_form = {
                'id': produto.id,
                'nome': nome,
                'preco': preco_str, 
                'descricao': descricao
            }
            return render_template('editar.html', produto=produto_form)
        
        # Se não houver erros, atualiza os dados
        produto.nome = nome
        produto.preco = float(preco_str)
        produto.descricao = descricao
        
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
    
    return render_template('editar.html', produto=produto)

# Nova rota para excluir produto
@app.route('/excluir/<int:id>', methods=['POST'])
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)
    
    try:
        nome_produto = produto.nome  # Guardar o nome para mostrar na mensagem
        db.session.delete(produto)
        db.session.commit()
        
        flash(f'Produto "{nome_produto}" excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir o produto: {str(e)}', 'danger')
    
    return redirect(url_for('listar_produtos'))

# Criar tabelas e inserir dados de exemplo
with app.app_context():
    db.create_all()
    
    # Adicionar produtos de exemplo se o banco estiver vazio
    if Produto.query.count() == 0:
        produtos_exemplo = [
            Produto(nome='Camiseta', preco=49.90, descricao='Camiseta 100% algodão, tamanho M'),
            Produto(nome='Calça Jeans', preco=99.90, descricao='Calça jeans azul, estilo casual, tamanho 42')
        ]
        db.session.add_all(produtos_exemplo)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
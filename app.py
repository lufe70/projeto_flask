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

# Modelo de Categoria
class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    
    # Relacionamento com produtos (um para muitos)
    produtos = db.relationship('Produto', backref='categoria', lazy=True)
    
    def __repr__(self):
        return f'<Categoria {self.nome}>'

# Modelo de Produto com relacionamento com categoria
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    
    # Chave estrangeira para Categoria
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id', name='fk_produto_categoria'), nullable=True)
    
    def __repr__(self):
        return f'<Produto {self.nome}>'

# Rota principal - lista produtos
@app.route('/')
def listar_produtos():
    # Opção de filtragem por categoria
    categoria_id = request.args.get('categoria', None)
    
    # Consulta base
    query = Produto.query
    
    # Aplicar filtro por categoria se solicitado
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            query = query.filter_by(categoria_id=categoria_id)
        except ValueError:
            # Ignora o filtro se o ID não for um número válido
            pass
    
    # Obter produtos e categorias para a view
    produtos = query.all()
    categorias = Categoria.query.order_by(Categoria.nome).all()
    
    return render_template('listar.html', 
                          produtos=produtos, 
                          categorias=categorias, 
                          categoria_filtro=categoria_id)

# Rota para adicionar produto
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_produto():
    # Obter todas as categorias para o select do formulário
    categorias = Categoria.query.order_by(Categoria.nome).all()
    
    if request.method == 'POST':
        # Extrair os dados do formulário
        nome = request.form.get('nome', '').strip()
        preco_str = request.form.get('preco', '').strip()
        descricao = request.form.get('descricao', '').strip()
        categoria_id = request.form.get('categoria_id', None)
        
        # Converter categoria_id para None se vazio ou para inteiro
        if categoria_id:
            try:
                categoria_id = int(categoria_id)
            except ValueError:
                categoria_id = None
        else:
            categoria_id = None
        
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
        
        # Verificar se a categoria existe se um ID foi fornecido
        if categoria_id:
            categoria = Categoria.query.get(categoria_id)
            if not categoria:
                errors.append('A categoria selecionada não existe.')
        
        # Se houver erros, mostre-os e volte ao formulário
        if errors:
            for error in errors:
                flash(error, 'danger')
            # Retorna ao formulário com os dados preenchidos para correção
            return render_template('adicionar.html', 
                                  produto={'nome': nome, 'preco': preco_str, 'descricao': descricao, 'categoria_id': categoria_id},
                                  categorias=categorias)
        
        # Se não houver erros, prossegue com a adição ao banco
        novo_produto = Produto(nome=nome, preco=preco, descricao=descricao, categoria_id=categoria_id)
        db.session.add(novo_produto)
        db.session.commit()
        
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
    
    return render_template('adicionar.html', categorias=categorias)

# Nova rota para editar produto
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    categorias = Categoria.query.order_by(Categoria.nome).all()
    
    if request.method == 'POST':
        # Extrair os dados do formulário
        nome = request.form.get('nome', '').strip()
        preco_str = request.form.get('preco', '').strip()
        descricao = request.form.get('descricao', '').strip()
        categoria_id = request.form.get('categoria_id', None)
        
        # Converter categoria_id para None se vazio ou para inteiro
        if categoria_id:
            try:
                categoria_id = int(categoria_id)
            except ValueError:
                categoria_id = None
        else:
            categoria_id = None
        
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
        
        # Verificar se a categoria existe se um ID foi fornecido
        if categoria_id:
            categoria = Categoria.query.get(categoria_id)
            if not categoria:
                errors.append('A categoria selecionada não existe.')
        
        # Se houver erros, mostre-os e volte ao formulário
        if errors:
            for error in errors:
                flash(error, 'danger')
            # Cria um dicionário com os dados atuais para preencher o formulário
            produto_form = {
                'id': produto.id,
                'nome': nome,
                'preco': preco_str, 
                'descricao': descricao,
                'categoria_id': categoria_id
            }
            return render_template('editar.html', produto=produto_form, categorias=categorias)
        
        # Se não houver erros, atualiza os dados
        produto.nome = nome
        produto.preco = float(preco_str)
        produto.descricao = descricao
        produto.categoria_id = categoria_id
        
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
    
    return render_template('editar.html', produto=produto, categorias=categorias)

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

# Rotas para gerenciar categorias
@app.route('/categorias')
def listar_categorias():
    categorias = Categoria.query.all()
    return render_template('categorias/listar.html', categorias=categorias)

@app.route('/categorias/adicionar', methods=['GET', 'POST'])
def adicionar_categoria():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        
        # Validação
        errors = []
        if not nome:
            errors.append('O nome da categoria é obrigatório.')
        elif len(nome) < 2:
            errors.append('O nome da categoria deve ter pelo menos 2 caracteres.')
        elif len(nome) > 50:
            errors.append('O nome da categoria não pode ter mais de 50 caracteres.')
        
        # Verificar se já existe categoria com este nome
        categoria_existente = Categoria.query.filter(Categoria.nome.ilike(nome)).first()
        if categoria_existente:
            errors.append(f'Já existe uma categoria com o nome "{nome}".')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('categorias/adicionar.html', categoria={'nome': nome})
        
        # Adicionar categoria
        nova_categoria = Categoria(nome=nome)
        db.session.add(nova_categoria)
        db.session.commit()
        
        flash(f'Categoria "{nome}" adicionada com sucesso!', 'success')
        return redirect(url_for('listar_categorias'))
    
    return render_template('categorias/adicionar.html')

@app.route('/categorias/editar/<int:id>', methods=['GET', 'POST'])
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        
        # Validação
        errors = []
        if not nome:
            errors.append('O nome da categoria é obrigatório.')
        elif len(nome) < 2:
            errors.append('O nome da categoria deve ter pelo menos 2 caracteres.')
        elif len(nome) > 50:
            errors.append('O nome da categoria não pode ter mais de 50 caracteres.')
        
        # Verificar se já existe outra categoria com este nome
        categoria_existente = Categoria.query.filter(Categoria.nome.ilike(nome), Categoria.id != id).first()
        if categoria_existente:
            errors.append(f'Já existe uma categoria com o nome "{nome}".')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('categorias/editar.html', categoria={'id': id, 'nome': nome})
        
        # Atualizar categoria
        categoria.nome = nome
        db.session.commit()
        
        flash(f'Categoria "{nome}" atualizada com sucesso!', 'success')
        return redirect(url_for('listar_categorias'))
    
    return render_template('categorias/editar.html', categoria=categoria)

@app.route('/categorias/excluir/<int:id>', methods=['POST'])
def excluir_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    
    # Verificar se existem produtos nesta categoria
    if categoria.produtos:
        flash(f'Não é possível excluir a categoria "{categoria.nome}" pois ela possui produtos vinculados.', 'danger')
        return redirect(url_for('listar_categorias'))
    
    try:
        nome_categoria = categoria.nome
        db.session.delete(categoria)
        db.session.commit()
        flash(f'Categoria "{nome_categoria}" excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir a categoria: {str(e)}', 'danger')
    
    return redirect(url_for('listar_categorias'))

# Criar tabelas e inserir dados de exemplo
with app.app_context():
    db.create_all()
    
    # Adicionar categorias de exemplo se o banco estiver vazio
    # if Categoria.query.count() == 0:
    #     categorias_exemplo = [
    #         Categoria(nome='Roupas'),
    #         Categoria(nome='Calçados'),
    #         Categoria(nome='Acessórios'),
    #         Categoria(nome='Eletrônicos')
    #     ]
    #     db.session.add_all(categorias_exemplo)
    #     db.session.commit()
    
    # Adicionar produtos de exemplo se o banco estiver vazio
    # if Produto.query.count() == 0:
    #     # Obter categorias
    #     categoria_roupas = Categoria.query.filter_by(nome='Roupas').first()
    #     categoria_acessorios = Categoria.query.filter_by(nome='Acessórios').first()
        
    #     produtos_exemplo = [
    #         Produto(nome='Camiseta', preco=49.90, descricao='Camiseta 100% algodão, tamanho M', 
    #                categoria_id=categoria_roupas.id if categoria_roupas else None),
    #         Produto(nome='Calça Jeans', preco=99.90, descricao='Calça jeans azul, estilo casual, tamanho 42',
    #                categoria_id=categoria_roupas.id if categoria_roupas else None),
    #         Produto(nome='Relógio', preco=199.90, descricao='Relógio esportivo à prova d\'água',
    #                categoria_id=categoria_acessorios.id if categoria_acessorios else None)
    #     ]
    #     db.session.add_all(produtos_exemplo)
    #     db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
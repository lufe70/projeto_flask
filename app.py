from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid

# Configuração para upload de imagens
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Criar o diretório de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicialização do Flask e configuração do banco de dados
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///produtos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'chave-secreta-para-flash-messages'  # Necessário para flash messages
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB para uploads
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

# Modelo de Produto com relacionamento com categoria e imagem
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    
    # Campos para imagem
    imagem_nome = db.Column(db.String(255), nullable=True)
    imagem_data = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Chave estrangeira para Categoria
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=True)
    
    def __repr__(self):
        return f'<Produto {self.nome}>'
        
    @property
    def imagem_url(self):
        """Retorna a URL da imagem do produto"""
        if self.imagem_nome:
            return f'/uploads/{self.imagem_nome}'
        return None

# Funções auxiliares para upload de arquivos
def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    """Salva a imagem e retorna o nome seguro do arquivo"""
    if file and allowed_file(file.filename):
        # Gerar um nome de arquivo único
        filename = secure_filename(file.filename)
        # Adicionar um UUID para garantir unicidade
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return unique_filename
    return None

# Rota para servir arquivos de upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rota para detalhes do produto
@app.route('/produto/<int:id>')
def detalhes_produto(id):
    produto = Produto.query.get_or_404(id)
    return render_template('detalhes.html', produto=produto)

# Rota principal - lista produtos
@app.route('/admin')
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
        
        # Validar imagem
        imagem_nome = None
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file.filename != '':
                if not allowed_file(file.filename):
                    errors.append('Formato de imagem não permitido. Use PNG, JPG, JPEG ou GIF.')
                else:
                    # A imagem será salva se não houver erros
                    pass
            
        # Se houver erros, mostre-os e volte ao formulário
        if errors:
            for error in errors:
                flash(error, 'danger')
            # Retorna ao formulário com os dados preenchidos para correção
            return render_template('adicionar.html', 
                                  produto={'nome': nome, 'preco': preco_str, 'descricao': descricao, 'categoria_id': categoria_id},
                                  categorias=categorias)
        
        # Processar o upload da imagem se foi enviada
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file.filename != '':
                imagem_nome = save_image(file)
        
        # Se não houver erros, prossegue com a adição ao banco
        novo_produto = Produto(
            nome=nome, 
            preco=preco, 
            descricao=descricao, 
            categoria_id=categoria_id,
            imagem_nome=imagem_nome
        )
        db.session.add(novo_produto)
        db.session.commit()
        
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
    
    return render_template('adicionar.html', categorias=categorias)

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
        manter_imagem = request.form.get('manter_imagem', 'false')
        
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
        
        # Validar imagem
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file.filename != '':
                if not allowed_file(file.filename):
                    errors.append('Formato de imagem não permitido. Use PNG, JPG, JPEG ou GIF.')
        
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
                'categoria_id': categoria_id,
                'imagem_nome': produto.imagem_nome
            }
            return render_template('editar.html', produto=produto_form, categorias=categorias)
        
        # Processar o upload da imagem se foi enviada e não está marcado para manter a atual
        if manter_imagem != 'true' and 'imagem' in request.files:
            file = request.files['imagem']
            if file.filename != '':
                # Remover imagem antiga se existir
                if produto.imagem_nome:
                    try:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], produto.imagem_nome)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        print(f"Erro ao excluir imagem antiga: {e}")
                
                # Salvar nova imagem
                produto.imagem_nome = save_image(file)
                produto.imagem_data = datetime.utcnow()
            elif manter_imagem != 'true' and not produto.imagem_nome:
                # Se não enviou imagem e escolheu não manter a atual, e não tinha imagem
                produto.imagem_nome = None
        elif manter_imagem != 'true':
            # Se escolheu não manter e não enviou nova imagem, remove a atual
            if produto.imagem_nome:
                try:
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], produto.imagem_nome)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                except Exception as e:
                    print(f"Erro ao excluir imagem: {e}")
            produto.imagem_nome = None
        
        # Se não houver erros, atualiza os dados
        produto.nome = nome
        produto.preco = float(preco_str)
        produto.descricao = descricao
        produto.categoria_id = categoria_id
        
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
    
    return render_template('editar.html', produto=produto, categorias=categorias)

@app.route('/excluir/<int:id>', methods=['POST'])
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)
    
    try:
        # Remover imagem se existir
        if produto.imagem_nome:
            try:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], produto.imagem_nome)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Erro ao excluir imagem: {e}")
        
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

# Adicione estas rotas ao final do seu app.py, antes da linha "if __name__ == '__main__':"

# Rota da loja com filtro por categoria
@app.route('/')
def loja():
    # Obter filtro de categoria
    categoria_id = request.args.get('categoria')
    
    # Filtrar produtos por categoria, se necessário
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            produtos = Produto.query.filter_by(categoria_id=categoria_id).all()
        except ValueError:
            produtos = Produto.query.all()
    else:
        produtos = Produto.query.all()
    
    # Obter todas as categorias para o menu
    categorias = Categoria.query.all()
    
    # Obter o carrinho da sessão
    carrinho = session.get('carrinho', [])
    total_itens = sum(item.get('quantidade', 0) for item in carrinho)
    
    return render_template('loja.html', 
                          produtos=produtos, 
                          categorias=categorias,
                          total_itens=total_itens,
                          categoria_atual=categoria_id)

# Rota para adicionar ao carrinho
@app.route('/adicionar_carrinho/<int:produto_id>', methods=['POST'])
def adicionar_carrinho(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    quantidade = int(request.form.get('quantidade', 1))
    
    # Inicializar o carrinho se não existir na sessão
    if 'carrinho' not in session:
        session['carrinho'] = []
    
    # Verificar se o produto já está no carrinho
    carrinho = session['carrinho']
    item_existente = next((item for item in carrinho if item['id'] == produto_id), None)
    
    if item_existente:
        # Atualizar quantidade se o produto já estiver no carrinho
        item_existente['quantidade'] += quantidade
        flash(f'Quantidade de {produto.nome} atualizada no carrinho!', 'success')
    else:
        # Adicionar novo item ao carrinho
        carrinho.append({
            'id': produto_id,
            'nome': produto.nome,
            'preco': produto.preco,
            'quantidade': quantidade,
            'imagem': produto.imagem_nome
        })
        flash(f'{produto.nome} adicionado ao carrinho!', 'success')
    
    # Atualizar a sessão
    session['carrinho'] = carrinho
    
    return redirect(url_for('loja'))

# Rota para visualizar carrinho
@app.route('/carrinho')
def ver_carrinho():
    carrinho = session.get('carrinho', [])
    total = sum(item['preco'] * item['quantidade'] for item in carrinho)
    
    return render_template('carrinho.html', carrinho=carrinho, total=total)

# Rota para esvaziar o carrinho
@app.route('/esvaziar_carrinho', methods=['POST'])
def esvaziar_carrinho():
    session.pop('carrinho', None)
    flash('Carrinho esvaziado com sucesso!', 'success')
    return redirect(url_for('ver_carrinho'))



# Criar tabelas e inserir dados de exemplo
with app.app_context():
    db.create_all()
    
    # # Adicionar categorias de exemplo se o banco estiver vazio
    # if Categoria.query.count() == 0:
    #     categorias_exemplo = [
    #         Categoria(nome='Roupas'),
    #         Categoria(nome='Calçados'),
    #         Categoria(nome='Acessórios'),
    #         Categoria(nome='Eletrônicos')
    #     ]
    #     db.session.add_all(categorias_exemplo)
    #     db.session.commit()
    
    # # Adicionar produtos de exemplo se o banco estiver vazio
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
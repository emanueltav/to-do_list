from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'curioso'

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    is_done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user is None:
        return redirect(url_for('login'))

    tasks = Task.query.filter_by(user_id=user.id).all()
    return render_template('home.html', tasks=tasks, user=user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not username or not password:
            return 'Preencha todos os campos!'

        if User.query.filter_by(username=username).first():
            return 'Usuário já existe!'

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('home'))
        return 'Credenciais inválidas!'

    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    title = request.form['title'].strip()
    description = request.form['description'].strip()

    if not title or not description:
        return 'Título e descrição são obrigatórios!'

    new_task = Task(title=title, description=description, user_id=session['user_id'])
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == session['user_id']:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/toggle/<int:task_id>')
def toggle_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == session['user_id']:
        task.is_done = not task.is_done
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/edit/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get(task_id)

    if not task or task.user_id != session['user_id']:
        return 'Tarefa não encontrada ou acesso negado.'

    title = request.form['title'].strip()
    description = request.form['description'].strip()

    if not title or not description:
        return 'Título e descrição são obrigatórios!'

    task.title = title
    task.description = description
    db.session.commit()

    return redirect(url_for('home'))


# 🚀 CRUD de Usuário

@app.route('/update_account', methods=['POST'])
def update_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    new_username = request.form['username'].strip()
    new_password = request.form['password'].strip()

    if not new_username or not new_password:
        return 'Preencha todos os campos!'

    existing_user = User.query.filter_by(username=new_username).first()
    if existing_user and existing_user.id != user.id:
        return 'Nome de usuário já está em uso.'

    user.username = new_username
    user.password = new_password
    db.session.commit()

    return redirect(url_for('home'))


@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    Task.query.filter_by(user_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()

    session.pop('user_id', None)

    return redirect(url_for('register'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
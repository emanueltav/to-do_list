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
    tasklists = db.relationship('TaskList', backref='user', lazy=True)
    tasks = db.relationship('Task', backref='user', lazy=True)


class TaskList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tasks = db.relationship('Task', backref='tasklist', lazy=True, cascade="all, delete-orphan")


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    is_done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tasklist_id = db.Column(db.Integer, db.ForeignKey('task_list.id'), nullable=False)


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

    user_id = session['user_id']

    lists = TaskList.query.filter_by(user_id=user_id).all()
    for task_list in lists:
        db.session.delete(task_list)

    tasks = Task.query.filter_by(user_id=user_id).all()
    for task in tasks:
        db.session.delete(task)

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)

    db.session.commit()
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user is None:
        return redirect(url_for('login'))

    task_lists = TaskList.query.filter_by(user_id=user.id).all()
    return render_template('to-do/list.html', task_lists=task_lists, user=user)


@app.route('/create_list', methods=['POST'])
def create_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = request.form['name'].strip()
    if not name:
        return 'Nome da lista é obrigatório!'

    new_list = TaskList(name=name, user_id=session['user_id'])
    db.session.add(new_list)
    db.session.commit()

    return redirect(url_for('home'))


@app.route('/list/<int:list_id>')
def view_list(list_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task_list = TaskList.query.get(list_id)
    if not task_list or task_list.user_id != session['user_id']:
        return 'Lista não encontrada ou acesso negado.'

    tasks = Task.query.filter_by(tasklist_id=task_list.id).all()
    return render_template('to-do/task.html', task_list=task_list, tasks=tasks)


@app.route('/edit_list/<int:list_id>', methods=['POST'])
def edit_list(list_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task_list = TaskList.query.get(list_id)
    if task_list and task_list.user_id == session['user_id']:
        new_name = request.form['name'].strip()
        if new_name:
            task_list.name = new_name
            db.session.commit()

    return redirect(url_for('home'))


@app.route('/delete_list/<int:list_id>')
def delete_list(list_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task_list = TaskList.query.get(list_id)
    if task_list and task_list.user_id == session['user_id']:
        db.session.delete(task_list)
        db.session.commit()

    return redirect(url_for('home'))


@app.route('/add_task/<int:list_id>', methods=['POST'])
def add_task(list_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task_list = TaskList.query.get(list_id)
    if not task_list or task_list.user_id != session['user_id']:
        return 'Lista não encontrada ou acesso negado.'

    title = request.form['title'].strip()
    description = request.form['description'].strip()

    if not title or not description:
        return 'Título e descrição são obrigatórios!'

    new_task = Task(
        title=title,
        description=description,
        user_id=session['user_id'],
        tasklist_id=list_id
    )
    db.session.add(new_task)
    db.session.commit()

    return redirect(url_for('view_list', list_id=list_id))


@app.route('/edit_task/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get(task_id)
    if task and task.user_id == session['user_id']:
        new_title = request.form['title'].strip()
        new_description = request.form['description'].strip()

        if new_title and new_description:
            task.title = new_title
            task.description = new_description
            db.session.commit()

        return redirect(url_for('view_list', list_id=task.tasklist_id))

    return redirect(url_for('home'))


@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get(task_id)

    if task and task.user_id == session['user_id']:
        list_id = task.tasklist_id
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('view_list', list_id=list_id))

    return redirect(url_for('home'))


@app.route('/toggle_task/<int:task_id>')
def toggle_task(task_id):
    task = Task.query.get(task_id)

    if task and task.user_id == session['user_id']:
        task.is_done = not task.is_done
        db.session.commit()
        return redirect(url_for('view_list', list_id=task.tasklist_id))

    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

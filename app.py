import os
from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_super_secret_key_123'
login_manager = LoginManager(app)
login_manager.login_view = 'login'
# Get the database URL from the environment (if on Render)
database_url = os.environ.get('DATABASE_URL')

# Fix a specific Render quirk (they use 'postgres://' but SQLAlchemy needs 'postgresql://')
if database_url and database_url.startswith("postgres://"):
  database_url = database_url.replace("postgres://", "postgresql://", 1)

# Use the cloud DB if found, otherwise use local sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///test.db'

db = SQLAlchemy(app)

class Todo(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  content = db.Column(db.String(200), nullable=False)
  date_created = db.Column(db.DateTime, default=datetime.utcnow)

  # NEW LINE: The link to the User table
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

  def __repr__(self):
    return '<Task %r>' % self.id

class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), nullable=False, unique=True)
  password_hash = db.Column(db.String(200), nullable=False)

  # NEW LINE: This isn't a column, it's a "magic link"
  tasks = db.relationship('Todo', backref='author', lazy=True)

  # ... keep your set_password and check_password methods below ...

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)
  
  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))
  
with app.app_context():
    db.create_all()


@app.route('/', methods=['POST', 'GET'])
def index():
  if request.method == 'POST':
    if not current_user.is_authenticated:
      return redirect('/login')
    
    task_content = request.form['content']
    # NEW: We add the author!
    new_task = Todo(content=task_content, author=current_user)

    try:
      db.session.add(new_task)
      db.session.commit()
      return redirect('/')
    except:
      return 'There was an issue adding your task'

  else:
    # NEW: Only fetch tasks if a user is actually logged in
    tasks = []
    if current_user.is_authenticated:
      tasks = current_user.tasks

    return render_template('index.html', tasks=tasks)
  
@app.route('/delete/<int:id>')
def delete(id):
  task_to_delete = Todo.query.get_or_404(id)

  try:
    db.session.delete(task_to_delete)
    db.session.commit()
    # We successfully deleted the task.
    # What line of code goes here to send the user back to the homepage?
    return redirect('/')
  except:
    return 'There was a problem deleting that task'

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
  task = Todo.query.get_or_404(id)

  if request.method == 'POST':
    task.content = request.form['content']

    try:
      db.session.commit()
      return redirect('/')
    except:
      return 'There was an issue updating your task'
  else:
    return render_template('update.html', task=task)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
      username = request.form['username']
      password = request.form['password']

      new_user = User(username=username)
      new_user.set_password(password)

      try:
        db.session.add(new_user)
        db.session.commit()
        return redirect('/')
      except:
        return "Username already exists"
    
    else:
      return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
      login_user(user)
      return redirect('/')
    
    # This runs if it's a GET request OR if the login failed above
  return render_template('login.html')

@app.route('/logout')
def logout():
  logout_user()
  return redirect('/login')

@app.route('/api/add', methods=['POST'])
@login_required
def add_task_api():
  # 1. Get the data from the "text message" (JSON)
  data = request.get_json()
  task_content = data.get('content')

  # 2. Save it to the database (Standard logic)
  new_task = Todo(content=task_content, author=current_user)
  db.session.add(new_task)
  db.session.commit()

  # 3. Send back a receipt (JSON), not a webpage! 

  return jsonify({
    'result': 'success',
    'id': new_task.id,
    'content': new_task.content,
    'date': new_task.date_created.strftime('%Y-%m-%d')
  })


if __name__ == '__main__':
  app.run(debug=True, port=8000)
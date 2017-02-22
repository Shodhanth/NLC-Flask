from flask import Flask
from flask import (
	render_template,
	send_file,
	send_from_directory,
	request,
	abort,
	redirect,
	g,
	url_for)
from werkzeug import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from decos import login_required
import hashlib
import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
# app.debug = False
app.debug = True
session = []
username = "root"
password = ''
usernumber = 0

UPLOAD_FOLDER = '/home/a0_/Flask/NLC/Uploads/'
ALL_PAPERS = '/home/a0_/Flask/NLC/Uploads/All/'
ALLOWED_EXTENSIONS = set(['pdf', 'PDF'])

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://'+username+':'+password+'@127.0.0.1/nlcweb'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# Database Model

class Announcements(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	announcements = db.Column(db.Text)
	created = db.Column(db.DateTime)

	def __init__(self, announcements):
		self.announcements = announcements
		self.created = datetime.datetime.now()

	def __repr__(self):
		return '<Announcements %r>' % self.id

class Users(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	password = db.Column(db.String(64), nullable=False)
	fullname = db.Column(db.String(200), nullable=False)
	college_name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(150), unique=True, nullable=False)
	phone = db.Column(db.String(10), nullable=False)
	project_name = db.Column(db.Text, nullable=False)
	file_location = db.Column(db.Text)

	def __init__(self, username, password, college_name, phone, project_name, email, fullname):
		self.username = username
		hash_pass = hashlib.md5(bytes(password, 'utf-8'))
		self.password = hash_pass.hexdigest()
		self.college_name = college_name
		self.phone = phone
		self.project_name = project_name
		self.email = email
		self.fullname = fullname

	def __repr__(self):
		return '<User %r>' % self.username

class Admin(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	password = db.Column(db.String(64), nullable=False)
	uploadable = db.Column(db.Boolean, default=True)

	def __init__(self, username, password):
		self.username = username
		hash_pass = hashlib.md5(bytes(password, 'utf-8'))
		self.password = hash_pass.hexdigest()

	def __repr__(self):
		return '<Admin %r>' % self.id

# End Database Models

# Utils

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def getUserNumber():
	usr = usernumber + 1
	return "%04d" % (usr ,)
# End Utils


# App Routes

@app.route('/')
def index():
	announcements = Announcements.query.order_by(desc(Announcements.created))
	return render_template('index.html', announcements=announcements)

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/committee')
def committee():
	return render_template('committee.html')

@app.route('/register', methods=['GET','POST'])
def register():
	if request.method == 'GET':
		return render_template('register.html')
	
	if request.method == 'POST':	
		email = request.form['email']
		college_name = request.form['college_name']
		phone = request.form['phone']
		project_name = request.form['project_name']
		password = request.form['password']
		fullname = request.form['fullname']
	# username, password, college_name, phone, project_name, fullname

		username = 'nlc' + getUserNumber()
		new_user = Users(username, password, college_name, phone, project_name, email, fullname)

		try:
			db.session.add(new_user)
			db.session.commit()
			return redirect(url_for('index'))
		except IntegrityError:
			return render_template('errors/user.html')

@app.route('/login', methods=['GET','POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password_form = request.form['password']
		hashd = hashlib.md5(bytes(password_form, 'utf-8'))
		hashd = hashd.hexdigest()
		user = Users.query.filter_by(username=username).first()

		if user.password == hashd :
			return render_template('login.html',user=user)
		else:
			return render_template('errors/403.html')

	# if request.method == 'GET':
	# 	users = Users.query.filter_by(username=user).first()
	# 	return render_template('login.html',user=user)


@app.route('/admin')
def admin():
	return render_template('admin.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
	username = request.form['username']
	password_form = request.form['password']
	hashd = hashlib.md5(bytes(password_form, 'utf-8'))
	hashd = hashd.hexdigest()
	user = Admin.query.filter_by(username=username).first()

	if user.password == hashd :
		return redirect(url_for('dashboard', user=user.username))
	else:
		return render_template('errors/403.html')

@app.route('/dashboard')
def dashboard():
	annonce = Announcements.query.all()
	users = Users.query.all()
	return render_template('dashboard.html',annonce=annonce,users=users)


@app.route('/dashboard/delete/<id>')
def dash_db(id):
	obj = Announcements.query.filter_by(id=id).first()
	try:
		db.session.delete(obj)
		db.session.commit()
		return redirect(url_for('dashboard'))
	except Exception as e:
		print(str(e))
		return render_template('errors/403.html')

@app.route('/upload/<user>', methods=['POST'])
def upload_paper(user):
	file_fd = request.files['paper']
	if file_fd and allowed_file(file_fd.filename):
		dirs = UPLOAD_FOLDER + str(user)
		if not os.path.exists(dirs):
			os.makedirs(dirs)
		filename = secure_filename(str(user+'.pdf'))
		file_fd.save(os.path.join(dirs, filename))


@app.route('/create')
def create_announcements():
	return render_template('announcement.html')

@app.route('/dash/new/<table>', methods=['POST'])
def new_dash_entry(table):
	if table == 'ann':
		announcement = request.form['announce']
		ann = Announcements(announcement)
		try:
			db.session.add(ann)
			db.session.commit()
			return redirect(url_for('dashboard'))
		except Exception as e:
			return render_template('errors/403.html')

@app.route('/papers/all', methods=['GET'])
def all_papers():
	user_files = []
	zip_path = ALL_PAPERS + 'papers.zip'	
	if not os.path.exists(ALL_PAPERS):
		os.makedirs(ALL_PAPERS)
	users = os.listdir(UPLOAD_FOLDER)
	users.remove('All')
	
	for user in users :
		user_files.append(UPLOAD_FOLDER + user + '/' + user + '.pdf')

	if os.path.isfile(zip_path) :
		os.remove(zip_path)
	import zipfile
	with zipfile.ZipFile(zip_path, 'w') as zf :
		for f in user_files :
			zf.write(f)
	return send_file(zip_path, as_attachment=True)		
		
@app.route('/paper/<path:path>')
def serve_paper(path):
	return send_from_directory('Uploads', path)

#returns the static files for all web pages and and when requested
@app.route('/static/<path:path>')
def server_static(path):
	try:
		return send_from_directory('static', path)
	except Exception:
		abort(404)
# End App Routes

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

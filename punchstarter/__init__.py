import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, render_template, request, url_for, redirect, abort
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Server
from flask.ext.security import Security, SQLAlchemyUserDatastore, login_required, current_user
from flask_mail import Mail
import datetime
import cloudinary.uploader

app = Flask(__name__)
app.config.from_object('punchstarter.default_settings')

# Enable database
db = SQLAlchemy(app)
migrate = Migrate(app,db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

# Has to be here, not at the top
# Has to be before Flask-Security
from punchstarter.models import *

# Setup Flask-Security
from forms import ExtendedRegisterForm
user_datastore = SQLAlchemyUserDatastore(db, Member, Role)
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

mail = Mail(app)

manager.add_command("runserver", Server(
    use_debugger = True,
    use_reloader = True,
    host = os.getenv('IP', '0.0.0.0'),
    port = int(os.getenv('PORT',5000))
    )
)

@app.route("/")
def index():
    projects = db.session.query(Project).order_by(Project.time_created.desc()).limit(15)
    return render_template("index.html", projects=projects)
    
@app.route("/projects/create/", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "GET":
        return render_template("create.html")
    elif request.method == "POST":
        # Handle the form submission
        
        now = datetime.datetime.now()
        time_end = request.form.get("funding_end_date")
        time_end = datetime.datetime.strptime(time_end, "%m/%d/%Y")
        
        # Upload cover photo
        
        cover_photo = request.files['cover_photo']
        uploaded_image = cloudinary.uploader.upload(
            cover_photo,
            crop = 'limit',
            width = 680,
            height = 550
        )
        image_filename = uploaded_image["public_id"]
        
        new_project = Project(
            member_id = current_user.id,
            name = request.form.get("project_name"),
            short_description = request.form.get("short_description"),
            long_description = request.form.get("long_description"),
            goal_amount = request.form.get("funding_goal"),
            image_filename = image_filename,
            time_start = now,
            time_end = time_end,
            time_created = now
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        return redirect(url_for("create_rewards", project_id=new_project.id))

@app.route("/projects/<int:project_id>/")
def project_detail(project_id):
    project = db.session.query(Project).get(project_id)
    if project is None:
        abort(404)
    
    return render_template("project_detail.html", project=project)

@app.route("/projects/<int:project_id>/rewards/", methods=["GET", "POST"])
@login_required
def create_rewards(project_id):
    project_query = db.session.query(Project).filter(Project.member_id == current_user.id, Project.id == project_id)
    if project_query.count() == 0:
        abort(404)
    
    project = project_query.one()
    
    if request.method == "GET":
        return render_template('create_rewards.html', project=project)
    elif request.method == "POST":
        titles = request.form.getlist('title[]')
        min_pledges = request.form.getlist('min_pledge[]')
        descriptions = request.form.getlist('description[]')
        
        for i in range(5):
            if titles[i] and descriptions[i] and min_pledges[i]:
                new_reward = Reward(
                    project_id = project.id,
                    title = titles[i],
                    description = descriptions[i],
                    minimum_pledge_amount = int(min_pledges[i])
                )
        
            db.session.add(new_reward)
        
        db.session.commit()
        
        return redirect(url_for('project_detail', project_id=project.id))
    
@app.route("/projects/<int:project_id>/pledge/", methods=["GET", "POST"])
def pledge(project_id):
    project = db.session.query(Project).get(project_id)
    if project is None:
        abort(404)
    if request.method == "GET":
        return render_template("pledge.html", project=project)
    elif request.method == "POST":
        # Handle the form submission
        
        new_pledge = Pledge (
            amount = request.form.get("amount"),
            time_created = datetime.datetime.now(),
            member_id = current_user.id,
            project_id = project.id
        )
        
        db.session.add(new_pledge)
        db.session.commit()
        
        return redirect(url_for("project_detail", project_id=project.id))

@app.route("/search/")
def search():
    query = request.args.get("q") or ""
    projects = db.session.query(Project).filter(
        Project.name.ilike('%'+query+'%') |
        Project.short_description.ilike('%'+query+'%') |
        Project.long_description.ilike('%'+query+'%')
    ).all()
    
    project_count = len(projects)
    
    return render_template('search.html',
        query_text=query,
        projects=projects,
        project_count=project_count
    )
    
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, render_template, request, url_for, redirect, abort
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Server
import datetime
import cloudinary.uploader

app = Flask(__name__)
app.config.from_object('punchstarter.default_settings')
manager = Manager(app)

db = SQLAlchemy(app)
migrate = Migrate(app,db)
manager.add_command('db', MigrateCommand)

# Has to be here, not at the top
from punchstarter.models import *

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
            member_id = 1, # Guest Creator
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
        
        return redirect(url_for("project_detail", project_id=new_project.id))

@app.route("/projects/<int:project_id>/")
def project_detail(project_id):
    project = db.session.query(Project).get(project_id)
    if project is None:
        abort(404)
    
    return render_template("project_detail.html", project=project)
    
@app.route("/projects/<int:project_id>/pledge/", methods=["GET", "POST"])
def pledge(project_id):
    project = db.session.query(Project).get(project_id)
    if project is None:
        abort(404)
    if request.method == "GET":
        return render_template("pledge.html", project=project)
    elif request.method == "POST":
        # Handle the form submission
        
        # Hardcode guest_pledgor for now
        guest_pledgor = db.session.query(Member).filter_by(id=2).one()
        
        new_pledge = Pledge (
            amount = request.form.get("amount"),
            time_created = datetime.datetime.now(),
            member_id = guest_pledgor.id,
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
    
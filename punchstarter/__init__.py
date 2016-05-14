import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, render_template, request, url_for, redirect, abort, flash, session
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Server
from flask.ext.security import Security, SQLAlchemyUserDatastore, login_required, current_user, user_registered
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

# Setup Stripe
import stripe
stripe.api_key = app.config["STRIPE_API_KEY"]

# Setup MixPanel
from mixpanel import Mixpanel
mp = Mixpanel(app.config["MIXPANEL_TOKEN"])

def mixpanel_register_new_user(sender, user, confirm_token, **extra):
    mp.people_set(user.id, {
        '$first_name': user.first_name,
        '$last_name': user.last_name,
        '$email': user.email
    })

user_registered.connect(mixpanel_register_new_user, app)

# @app.context_processor
# def navbar_context_processor():
#     categories = db.session.query(Category).all()
#     return dict(categories=categories)

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
            # category_id = request.form.get("category_id"),
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
@login_required
def pledge(project_id):
    project = db.session.query(Project).get(project_id)
    if project is None:
        abort(404)
    if request.method == "GET":
        return render_template("pledge.html", project=project)
    elif request.method == "POST":
        # Handle the form submission
        
        amount = int(request.form.get("amount") or 0)
        reward_id = request.form.get("reward_id")
        
        if reward_id == "none":
            reward_id = None
        else:
            # Valdations
            
            reward_query = db.session.query(Reward).filter(Reward.project_id == project.id, Reward.id == reward_id)
            if reward_query.count() == 0:
                flash("Please choose a pledge reward.")
                return redirect(url_for('pledge', project_id=project.id))
            reward = reward_query.one()
            
            if amount < reward.minimum_pledge_amount:
                flash("You must pledge at least $%s for that reward." % reward.minimum_pledge_amount)
                return redirect(url_for('pledge', project_id=project.id))
            
            if amount < 1:
                flash("You must pledge at least $1.")
        
        # Set session variables
        session['pledge_reward_id'] = reward_id
        session['pledge_amount'] = amount
        
        return redirect(url_for("pledge_confirm", project_id=project.id))

@app.route("/projects/<int:project_id>/pledge/confirm/", methods=["GET", "POST"])
@login_required
def pledge_confirm(project_id):
    project = db.session.query(Project).get(project_id)
    if project is None:
        abort(404)
    
    if request.method == "GET":
        reward = None
        if session['pledge_reward_id'] is not None:
            reward = db.session.query(Reward).get(session['pledge_reward_id'])
            
        return render_template('pledge_confirm.html',
            project=project,
            reward=reward,
            pledge_amount=session['pledge_amount']
        )
        
    elif request.method == "POST":
        stripe_token = request.form.get("stripe_token")
        
        description = "$%s pledge to %s from %s %s." % (
            session['pledge_amount'],
            project.name,
            current_user.first_name,
            current_user.last_name
        )
            
        stripe.Charge.create(
            amount=session['pledge_amount'] * 100, # amount in cents
            currency="usd",
            source=stripe_token, # obtained with Stripe.js
            description=description
        )
        
        new_pledge = Pledge (
            amount = session['pledge_amount'],
            reward_id = session['pledge_reward_id'],
            time_created = datetime.datetime.now(),
            member_id = current_user.id,
            project_id = project.id
        )
        
        db.session.add(new_pledge)
        db.session.commit()
        
        mp.track(current_user.id, 'Made Pledge', {'Amount': session['pledge_amount']})
        
        # Unset session variables
        session['pledge_reward_id'] = None
        session['pledge_amount'] = None
        
        return redirect(url_for('project_detail', project_id=project.id))

@app.route("/projects/<int:project_id>/stats/")
def stats(project_id):
    project = db.session.query(Project).get(project_id)
    if project is None:
        abort(404)
    
    return render_template('stats.html', project=project)

@app.route("/search/")
# @app.route("/search/category/<category_slug>")
def search(category_slug=None):
    query = request.args.get("q") or ""
    projects = db.session.query(Project).filter(
        Project.name.ilike('%'+query+'%') |
        Project.short_description.ilike('%'+query+'%') |
        Project.long_description.ilike('%'+query+'%')
    )
    
    # if category_slug:
        # projects = projects.filter(Category.id == Project.category_id).filter(Category.slug==category_slug)
    
    projects = projects.all()
    
    project_count = len(projects)
    
    # Set Query Text
    if category_slug:
        try:
            category = db.session.query(Category).filter_by(slug=category_slug).one()
            query_text = category.name
        except NoResultFound:
            query_text = category_slug
    
    else:
        query_text = query if query !="" else "all projects"
    
    return render_template('search.html',
        query_text=query,
        projects=projects,
        project_count=project_count
    )
    
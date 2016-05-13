from punchstarter import db
from sqlalchemy.sql import func
from flask.ext.security import RoleMixin, UserMixin
import datetime
import cloudinary.utils

roles_members = db.Table('roles_members',
    db.Column('member_id', db.Integer, db.ForeignKey('member.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
    )

class Member(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.String(255))
    confirmed_at = db.Column(db.DateTime)
    project = db.relationship('Project', backref='creator') # Called creator because a project's member is called a creator
    pledges = db.relationship('Pledge', backref='pledgor', foreign_keys='Pledge.member_id') # Have to specify the foreign key because there are multiple in Pledge
    roles = db.relationship('Role', secondary=roles_members, backref=db.backref('members', lazy='dynamic'))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    name = db.Column(db.String(100))
    short_description = db.Column(db.Text)
    long_description = db.Column(db.Text)
    goal_amount = db.Column(db.Integer)
    image_filename = db.Column(db.String(200)) # holds url from cloudinary
    time_start = db.Column(db.DateTime)
    time_end = db.Column(db.DateTime)
    time_created = db.Column(db.DateTime)
    pledges = db.relationship('Pledge', backref='project', lazy='dynamic', foreign_keys='Pledge.project_id')
    rewards = db.relationship('Reward', backref='project', lazy='dynamic', foreign_keys='Reward.project_id')
    
    @property
    def num_pledges(self):
        return self.pledges.count()
        
    @property
    def total_pledges(self):
        total_pledges = db.session.query(func.sum(Pledge.amount)).filter(Pledge.project_id==self.id).one()[0]
        if total_pledges is None:
            total_pledges = 0
            
        return total_pledges
        
    @property
    def percentage_funded(self):
        return int(self.total_pledges*100 / self.goal_amount)
    
    @property
    def num_days_left(self):
        now = datetime.datetime.now()
        num_days_left = (self.time_end - now).days
        
        return num_days_left
    
    @property
    def image_path(self):
        return cloudinary.utils.cloudinary_url(self.image_filename)[0]
        
    @property
    def duration(self):
        return (self.time_end - self.time_start).days
        
    def get_num_pledges_datapoints(self):
        pledges_per_day = db.session.query(
            func.date(Pledge.time_created),
            func.count(Pledge.time_created)
        ).filter(
            Project.id==self.id,
            Project.id==Pledge.project_id
        ).group_by(
            func.date(Pledge.time_created)
        ).all()
        
        datapoints = [[i+1,0] for i in range(self.duration + 2)] # [(0,0), (1,0), ..., (30,0)]
        for p in pledges_per_day:
            time_pledged = datetime.datetime.strptime(p[0], "%Y-%m-%d")
            day_num = (time_pledged.date() - self.time_start.date()).days
            num_pledges = p[1]
            
            datapoints[day_num] = [day_num, num_pledges]
        
        return datapoints
        
    def get_amount_pledged_datapoints(self):
        pledges_per_day = db.session.query(
            func.date(Pledge.time_created),
            func.sum(Pledge.amount)
        ).filter(
            Project.id==self.id,
            Project.id==Pledge.project_id
        ).group_by(
            func.date(Pledge.time_created)
        ).all()
        
        datapoints = [[i+1,0] for i in range(self.duration + 2)] # [(0,0), (1,0), ..., (30,0)]
        for p in pledges_per_day:
            time_pledged = datetime.datetime.strptime(p[0], "%Y-%m-%d")
            day_num = (time_pledged.date() - self.time_start.date()).days
            amount = p[1]
            
            datapoints[day_num] = [day_num, amount]
        
        return datapoints
    
class Pledge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer)
    time_created = db.Column(db.DateTime)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    reward_id = db.Column(db.Integer, db.ForeignKey('reward.id'), nullable=True)

class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)
    minimum_pledge_amount = db.Column(db.Integer, nullable=False)
    pledges = db.relationship('Pledge', backref='pledge', lazy='dynamic', foreign_keys='Pledge.reward_id')
    
    @property
    def num_pledges(self):
        return self.pledges.count()
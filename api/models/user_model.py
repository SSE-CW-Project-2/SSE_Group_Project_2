####################################################################################################
# Project Name: Motive Event Management System
# File: user_model.py
# Description: This file contains the database models for users within the Motion Event Management
#              System.
#
#              It defines a base User model with common attributes for all user types and
#              specialized models for Establishments (venues), Entertainers, and Individual Users,
#              leveraging inheritance to extend the base User model. This structure supports the
#              complex interactions between different user types, including hosting events,
#              performing at events, and purchasing tickets.
#
#              Establishments host events, Entertainers apply for gigs at these events, and
#              Individual Users purchase tickets to attend.
#
# Authors:
# Date: 2024-02-14
# Version: 1.0
#
# Notes: This model uses Flask-SQLAlchemy for ORM functionality. It's designed to be flexible,
#        allowing for future enhancements such as adding more user types or attributes.
####################################################################################################

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Base User model, which establishments, entertainers and individuals inherit from
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }


# Establishment model
class Establishment(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    events = db.relationship('Event', backref='establishment', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'establishment',
    }


# Entertainer model
class Entertainer(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    genres = db.Column(db.String(200))  # Just an example of a unique attribute
    gigs = db.relationship('Event', secondary='gig_entertainers', backref=db.backref('entertainers', lazy='dynamic'))

    __mapper_args__ = {
        'polymorphic_identity': 'entertainer',
    }


# Individual User model
class IndividualUser(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    tickets_purchased = db.relationship('Ticket', backref='individual', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'individual',
    }


# Event model to be hosted by Establishments - does not inherit from User
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    establishment_id = db.Column(db.Integer, db.ForeignKey('establishment.id'), nullable=False)


# Association table for Entertainers and Events
gig_entertainers = db.Table('gig_entertainers',
                            db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True),
                            db.Column('entertainer_id', db.Integer, db.ForeignKey('entertainer.id'), primary_key=True)
                            )


# Ticket model for events purchased by Individual Users - does not inherit from User
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    individual_id = db.Column(db.Integer, db.ForeignKey('individual.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

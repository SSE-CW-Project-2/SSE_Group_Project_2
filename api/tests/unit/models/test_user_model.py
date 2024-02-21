####################################################################################################
# Project Name: Motive Event Management System
# File: test_user_model.py
# Description: This file contains the unit tests for functionality and integrity of the classes
#              defined in user_model.py.
#
# Authors:
# Date: 2024-02-14
# Version: 1.0
#
# Notes:
####################################################################################################

from models.user_model.py import Establishment


# Testing that Establishment objects are created with the correct attributes
def test_establishment_creation(session):
    events = ["event1", "event2", "event3"]
    user = Establishment(
        id="2",
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        type="Type",
        events=events,
    )
    session.add(user)
    session.commit()

    retrieved_user = session.query(Establishment).filter_by(username="testuser").first()
    assert retrieved_user is not None
    assert retrieved_user.id == "2"
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.password_hash == "hash"
    assert retrieved_user.type == "Type"
    assert retrieved_user.events == events


# Testing blank Establishment constructor
def test_establishment_creation_blank(session):
    user = Establishment()
    session.add(user)
    session.commit()

    retrieved_user = session.query(Establishment).filter_by(username="testuser").first()
    assert retrieved_user is not None
    # Should be set up so that every user has an ID automatically
    assert retrieved_user.id is None
    assert retrieved_user.email is None
    assert retrieved_user.password_hash is None
    assert retrieved_user.type is None
    assert retrieved_user.events is None


# Testing that Establishment objects are created with the correct attributes
def test_establishment_creation_with_correct_attributes(session):
    events = ["event1", "event2", "event3"]
    user = Establishment(
        id="2",
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        type="Type",
        events=events,
    )
    session.add(user)
    session.commit()

    retrieved_user = session.query(Establishment).filter_by(username="testuser").first()
    assert retrieved_user is not None
    assert retrieved_user.id == "2"
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.password_hash == "hash"
    assert retrieved_user.type == "Type"
    assert retrieved_user.events == events

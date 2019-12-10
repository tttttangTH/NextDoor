
from app.models import Connection, User
from app import db


def is_friends_or_pending(user_a_id, user_b_id):
    """
    Checks the friend status between user_a and user_b.
    Checks if user_a and user_b are friends.
    Checks if there is a pending friend request from user_a to user_b.
    """

    is_friends = db.session.query(Connection).filter(Connection.user_a_id == user_a_id,
                                                     Connection.user_b_id == user_b_id,
                                                     Connection.status == "Accepted").first()

    is_pending = db.session.query(Connection).filter(Connection.user_a_id == user_a_id,
                                                     Connection.user_b_id == user_b_id,
                                                     Connection.status == "Requested").first()

    return is_friends, is_pending



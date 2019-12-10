from app import app, db, csrf
from flask import render_template


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@csrf.error_handler
def csrf_error(reason):
    return render_template('csrf_error.html', reason=reason), 400

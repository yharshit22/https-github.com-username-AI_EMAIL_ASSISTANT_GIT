from flask import Blueprint
from app import db

bp = Blueprint('main', __name__)

from app.main import routes
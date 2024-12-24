from flask import Flask, render_template, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import uuid
import datetime


from routes import user

from routes import category

from routes import product


from routes import pos
from flask import Flask 
from flask_cors import CORS

from app.routes.upload_routes import upload_bp
from app.routes.analytics_routes import analytics_bp

def create_app():
    app = Flask(__name__)
    
    app.config.from_object('app.config.Config')

    CORS(app)

    app.register_blueprint(upload_bp)
    app.register_blueprint(analytics_bp)

    return app
from .campus_routes import campus_bp
from .courses_routes import courses_bp
from .disciplines_routes import disciplines_bp
from .offers_routes import offers_bp
from .periods_routes import periods_bp
from .rooms_routes import rooms_bp
from .teachers_routes import teachers_bp
from .types_routes import types_bp
from internal_apis.professor_endpoint.professor_endpoint import deactivate_teacher_bp

def setup_rest_routes(app):

    app.register_blueprint(campus_bp, url_prefix="/restapi/campus")
    app.register_blueprint(courses_bp, url_prefix="/restapi/courses/")
    app.register_blueprint(disciplines_bp, url_prefix="/restapi/disciplines/")
    app.register_blueprint(offers_bp, url_prefix="/restapi/offers")
    app.register_blueprint(periods_bp, url_prefix="/restapi/periods/")
    app.register_blueprint(rooms_bp, url_prefix="/restapi/rooms")
    app.register_blueprint(teachers_bp, url_prefix="/restapi/teachers")
    app.register_blueprint(types_bp, url_prefix="/restapi/types/")
    app.register_blueprint(deactivate_teacher_bp, url_prefix="/restapi/teachers/softdel/")




from flask import Blueprint, jsonify, request
from flasgger import swag_from
from internal_apis.src.utils.auth import check_api_key
from DAL import Campus
from auth_routes import token_required
from utils import log_info_request, log_resource_not_found, get_swagger_specification
from backpressure.individual_leaky_bucket import LeakyBucket

campus_bp = Blueprint('campus_bp', __name__, url_prefix="/campus")

spec = get_swagger_specification(path="campus", method="GET")
@campus_bp.route("/", methods=["GET"])
@LeakyBucket.individual_leaky_bucket(bucketcapacity=5, leakrate=0.7, keytimeout=25)
@log_info_request
@swag_from(spec)
def get_campus():
    campus_id = request.args.get("campus_id")
    if campus_id:
        try:
            return get_campus_by_id(campus_id)
        except Campus.DoesNotExist:
            log_resource_not_found("Campus", "campus_id", campus_id)
            return jsonify({"error": "Campus not found"}), 404

    campus_name = request.args.get("campus_name")
    if campus_name:
        try:
            return get_campus_by_name(campus_name)
        except Campus.DoesNotExist:
            log_resource_not_found("Campus", "campus_name", campus_name)
            return jsonify({"error": "Campus not found"}), 404

    campuses = Campus.objects.all()
    return jsonify([{"id": c.id, "name": c.name} for c in campuses])


def get_campus_by_id(campus_id):
    campus = Campus.objects.get(id=campus_id)
    if campus:
        return jsonify({"id": campus.id, "name": campus.name})


def get_campus_by_name(course_name):
    campus = Campus.objects.filter(name__icontains=course_name)
    if campus:
        return format_campus_response(campus)


def format_campus_response(campus):

    return jsonify([
        {
            "id": str(c.id),
            "name": c.name
        }
        for c in campus
    ])

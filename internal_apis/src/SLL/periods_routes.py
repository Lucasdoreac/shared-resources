from flasgger import swag_from
from flask import Blueprint, jsonify, request

from DAL import Period
from utils import log_info_request, log_resource_not_found, get_swagger_specification

periods_bp = Blueprint('periods_bp', __name__, url_prefix="/periods")

@periods_bp.route("/", methods=["GET"])
@log_info_request
@swag_from(get_swagger_specification(path="periods", method="GET"))
def get_periods():
    period_id = request.args.get("period_id")
    if period_id:
        try:
            return get_period_by_id(period_id)
        except Period.DoesNotExist:
            log_resource_not_found("Period","period_id" , period_id)
            return jsonify({"message": "Period does not exist"}), 404

    period_name = request.args.get("period_name")
    if period_name:
        try:
            return get_period_by_name(period_name)
        except Period.DoesNotExist:
            log_resource_not_found("Period","period_name" , period_name)
            return jsonify({"message": "Period does not exist"}), 404

    periods = Period.objects.all()
    return jsonify([{"id": p.id, "name": p.name} for p in periods])

def get_period_by_id(period_id):
    period = Period.objects.get(id=period_id)
    if period:
        return jsonify({"id": period.id, "name": period.name})


def get_period_by_name(period_name):
    period = Period.objects.filter(name__icontains=period_name)
    if period:
        return format_periods_response(period)


def format_periods_response(periods):

    return jsonify([
        {
            "id": str(p.id),
            "name": p.name
        }
        for p in periods
    ])

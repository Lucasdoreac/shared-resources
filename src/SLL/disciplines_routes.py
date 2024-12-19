from flasgger import swag_from
from flask import Blueprint, jsonify, request

from DAL import Discipline
from utils import log_info_request, log_resource_not_found, get_swagger_specification

disciplines_bp = Blueprint('disciplines_bp', __name__, url_prefix="/disciplines")

spec = get_swagger_specification(path="disciplines", method="GET")
print("swag:", spec)
@disciplines_bp.route("/", methods=["GET"])
@log_info_request
@swag_from(spec)
def get_disciplines():
    discipline_id = request.args.get("discipline_id")
    if discipline_id:
        try:
            return get_discipline_by_id(discipline_id)
        except Discipline.DoesNotExist:
            log_resource_not_found("Discipline", "discipline_id", discipline_id)
            return jsonify({"message": "Discipline not found"}), 404

    discipline_name = request.args.get("discipline_name")
    if discipline_name:
        try:
            return filter_discipline_by_name(discipline_name)
        except Discipline.DoesNotExist:
            log_resource_not_found("Discipline", "discipline_name", discipline_name)
            return jsonify({"message": "Discipline not found"}), 404

    course_id = request.args.get("course_id")
    if course_id:
        try:
            return filter_discipline_by_course(course_id)
        except Discipline.DoesNotExist:
            log_resource_not_found("Discipline", "course_id", course_id)
            return jsonify({"error": "Discipline not found"}), 404

    disciplines_queryset = Discipline.objects()

    return format_disciplines_response(disciplines_queryset)

def get_discipline_by_id(discipline_id):
    discipline = Discipline.objects.get(id=discipline_id)
    if discipline:
        return jsonify({
            "id": discipline.id,
            "name": discipline.name,
            "course": discipline.course,
            "workload": discipline.workload
        })

def filter_discipline_by_name(discipline_name):
    discipline = Discipline.objects.filter(name__icontains=discipline_name)
    if discipline:
        return format_disciplines_response(discipline)

def filter_discipline_by_course(course_id):
    discipline = Discipline.objects.filter(course__icontains=course_id)
    if discipline:
        return format_disciplines_response(discipline)


def pagination_config(base_queryset):
    page = request.args.get("page", 1, type=int)
    pagesize = request.args.get("pagesize", 10, type=int)
    skip = (page - 1) * pagesize

    result = base_queryset.skip(skip).limit(pagesize)

    return result, page, pagesize

def format_disciplines_response(base_queryset):
    total_count = base_queryset.count()

    result, page, pagesize = pagination_config(base_queryset)

    response_data = [
        {
            "id": str(r.id),
            "name": r.name,
            "course": r.course,
            "workload": r.workload
        }
        for r in result
    ]

    total_pages = (total_count + pagesize - 1) // pagesize if pagesize > 0 else 1
    return jsonify({
        "data": response_data,
        "pagination": {
            "page": page,
            "pagesize": pagesize,
            "total_count": total_count,
            "total_pages": total_pages
        }
    })
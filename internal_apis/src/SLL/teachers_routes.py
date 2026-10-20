import flask_caching
from flasgger import swag_from
from flask import Blueprint, jsonify, request
from DAL import Teacher
from utils.cache import cache
from utils import log_info_request, log_resource_not_found, get_swagger_specification

teachers_bp = Blueprint('teachers_bp', __name__, url_prefix="/teachers")

spec = get_swagger_specification(path="teachers", method="GET")


@teachers_bp.route("/", methods=["GET"])
@log_info_request
@swag_from(spec)
@cache.cached(timeout=43200, query_string=True)  # Cache for 12 hours
def get_teachers():
    teacher_id = request.args.get("teacher_id")
    if teacher_id:
        try:
            return get_teacher_by_id(teacher_id)
        except Teacher.DoesNotExist:
            log_resource_not_found("Teacher", "teacher_id", teacher_id)
            return jsonify({"error": "Teacher not found"}), 404

    teacher_name = request.args.get("teacher_name")
    if teacher_name:
        try:
            return filter_teacher_by_name(teacher_name)
        except Teacher.DoesNotExist:
            log_resource_not_found("Teacher", "teacher_name", teacher_name)
            return jsonify({"error": "Teacher not found"}), 404

    course_id = request.args.get("course_id")
    if course_id:
        try:
            return filter_teacher_by_course_id(course_id)
        except Teacher.DoesNotExist:
            log_resource_not_found("Teacher", "course_id", course_id)
            return jsonify({"error": "Teacher not found"}), 404

    teachers_queryset = Teacher.objects()
    return format_teacher_response(teachers_queryset)


def get_teacher_by_id(teacher_id):
    result = Teacher.objects.get(id=teacher_id)
    if result:
        return jsonify({
            "id": result.id,
            "name": result.name,
            "course_id": result.course,
            "email": result.email if result.email else None,

        })


def filter_teacher_by_name(teacher_name):
    result = Teacher.objects.filter(name__icontains=teacher_name)
    if result:
        return format_teacher_response(result)


def filter_teacher_by_course_id(course_id):
    result = Teacher.objects.filter(course=course_id)
    if result:
        return format_teacher_response(result)


def pagination_config(base_queryset):
    page = request.args.get("page", 1, type=int)
    pagesize = request.args.get("pagesize", 10, type=int)
    skip = (page - 1) * pagesize

    result = base_queryset.skip(skip).limit(pagesize)

    return result, page, pagesize


def format_teacher_response(base_queryset):
    total_count = base_queryset.count()

    result, page, pagesize = pagination_config(base_queryset)

    response_data = [
        {
            "id": str(r.id),
            "name": r.name,
            "course": r.course,
            "email": r.email if r.email else None,
            "active": r.active
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


import flask_caching
from flasgger import swag_from
from flask import Blueprint, jsonify, request

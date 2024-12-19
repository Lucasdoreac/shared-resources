from flask import Blueprint, jsonify, request
from flasgger import swag_from

from DAL import Course
from utils import log_info_request, log_resource_not_found, get_swagger_specification

courses_bp = Blueprint('courses_bp', __name__, url_prefix="/courses")

spec = get_swagger_specification(path="courses", method="GET")
print("swag:", spec)
@courses_bp.route("/", methods=["GET"])
@log_info_request
@swag_from(spec)
def get_all_courses():
    course_id = request.args.get("course_id")
    if course_id:
        try:
            return get_course_by_id(course_id)
        except Course.DoesNotExist:
            log_resource_not_found("Course", "course_id", course_id)
            return jsonify({"message": "Course not found"}), 404

    course_name = request.args.get("course_name")
    if course_name:
        try:
            return get_course_by_name(course_name)
        except Course.DoesNotExist:
            log_resource_not_found("Course", "course_name", course_name)
            return jsonify({"message": "Course not found"}), 404

    courses_queryset = Course.objects()

    return  format_courses_response(courses_queryset)

def get_course_by_id(course_id):
    course = Course.objects.get(id=course_id)
    if course:
        return jsonify({"id": course.id, "name": course.name})


def get_course_by_name(course_name):
    course = Course.objects.filter(name__icontains=course_name)
    if course:
        return format_courses_response(course)


def pagination_config(base_queryset):
    page = request.args.get("page", 1, type=int)
    pagesize = request.args.get("pagesize", 10, type=int)
    skip = (page - 1) * pagesize

    result = base_queryset.skip(skip).limit(pagesize)

    return result, page, pagesize

def format_courses_response(base_queryset):
    total_count = base_queryset.count()

    result, page, pagesize = pagination_config(base_queryset)

    response_data = [
        {
            "id": str(r.id),
            "name": r.name,
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
from flasgger import swag_from
from flask import Blueprint, jsonify, request

from DAL import Room
from utils import log_info_request, log_resource_not_found, get_swagger_specification

rooms_bp = Blueprint('rooms_bp', __name__, url_prefix="/rooms")

spec = get_swagger_specification(path="rooms", method="GET")
print("swag:", spec)
@rooms_bp.route("/", methods=["GET"])
@log_info_request
@swag_from(spec)
def get_rooms():
    room_id = request.args.get("room_id")
    if room_id:
        try:
            return get_room_by_id(room_id)
        except Room.DoesNotExist:
            log_resource_not_found("Room", "room_id", room_id)
            return jsonify({"message": "Room not found"}), 404

    room_name = request.args.get("room_name")
    if room_name:
        try:
            return filter_room_by_name(room_name)
        except Room.DoesNotExist:
            log_resource_not_found("Room", "room_name", room_name)
            return jsonify({"message": "Room not found"}), 404

    campus = request.args.get("campus")
    if campus:
        try:
            return filter_room_by_campus(campus)
        except Room.DoesNotExist:
            log_resource_not_found("Room", "campus", campus)
            return jsonify({"message": "Room not found"}), 404

    room_queryset = Room.objects()

    return format_rooms_response(room_queryset)

def get_room_by_id(room_id):
    result = Room.objects.get(id=room_id)
    if result:
        return jsonify({
            "id": result.id,
            "name": result.name,
            "campus": result.campus
        })

def filter_room_by_name(room_name):
    result = Room.objects.filter(name__icontains=room_name)
    if result:
        return format_rooms_response(result)

def filter_room_by_campus(campus):
    result = Room.objects.filter(campus__icontains=campus)
    if result:
        return format_rooms_response(result)

def pagination_config(base_queryset):
    page = request.args.get("page", 1, type=int)
    pagesize = request.args.get("pagesize", 10, type=int)
    skip = (page - 1) * pagesize

    result = base_queryset.skip(skip).limit(pagesize)

    return result, page, pagesize


def format_rooms_response(base_queryset):
    total_count = base_queryset.count()

    result, page, pagesize = pagination_config(base_queryset)

    response_data = [
        {
            "id": str(r.id),
            "name": r.name,
            "campus": r.campus
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

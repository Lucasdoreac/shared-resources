from flasgger import swag_from
from flask import Blueprint, jsonify, request
import datetime

from DAL import Offer, Campus, Discipline, Period, Room, Teacher
from utils import log_info_request, log_resource_not_found, check_api_key, get_swagger_specification

offers_bp = Blueprint('offer_bp', __name__, url_prefix="/offers") # Revisar

spec = get_swagger_specification(path="offers", method="GET")
@offers_bp.route('/', methods=['GET'])
@log_info_request
@swag_from(spec)
def get_offers():
    _id = request.args.get("id")
    if _id:
        return filter_entity("_id", _id)

    campus_id = request.args.get("campus_id")
    if campus_id:
        return filter_entity("campus", campus_id)

    course_id = request.args.get("course_id")
    if course_id:
        return filter_entity("course", course_id)

    discipline_id = request.args.get("discipline_id")
    if discipline_id:
        return filter_entity("discipline", discipline_id)

    period_id = request.args.get("period_id")
    if period_id:
        return filter_entity("period", period_id)

    room_id = request.args.get("room_id")
    if room_id:
        return filter_entity("room", room_id)

    teacher_id = request.args.get("teacher_id")
    if teacher_id:
        return filter_entity("teacher", teacher_id)

    total_enrolled = request.args.get("total_enrolled")
    if total_enrolled:
        return filter_entity("total_enrolled", total_enrolled)

    ## add fields HERE
    total_optatives_enrolled = request.args.get("total_optatives_enrolled")
    if total_optatives_enrolled:
        return filter_entity("total_optatives_enrolled", total_optatives_enrolled)

    year = request.args.get("year")
    if year:
        return filter_entity("year", year)

    semester = request.args.get("semester")
    if semester:
        return filter_entity("semester", semester)

    offer_id = request.args.get("offer_id")
    if offer_id:
        return filter_entity("offer_id", offer_id)


    offers_queryset = Offer.objects()

    return format_offers_response(offers_queryset)

spec_post = get_swagger_specification(path="offers", method="POST")
@offers_bp.route('/', methods=['POST'])
@check_api_key
@swag_from(spec_post)
def create_offer():
    data = request.get_json()
    try:
        # Validar e buscar entidades relacionadas
        campus = get_entity(Campus, data["campus"])
        discipline = get_entity(Discipline, data["discipline"])
        period = get_entity(Period, data["period"])
        room = get_entity(Room, data["room"])
        teacher = get_entity(Teacher, data["teacher"])

        missing_entities = [e for e in [campus, discipline, period, room, teacher] if e is None]
        if missing_entities:
            return jsonify({"error": "One or more related entities not found"}), 400

        # Criar oferta
        offer = Offer(
            discipline=discipline.id,
            period=period.id,
            campus=campus.id,
            room=room.id,
            teacher=teacher.id,
            total_enrolled=data["total_enrolled"],
            total_optatives_enrolled=data["total_optatives_enrolled"] if "total_optatives_enrolled" in data else 0,
            year=datetime.date.today().year,
            semester=1 if datetime.date.today().month < 7 else 2,
        )
        offer.save()

        return jsonify({"message": "Offer created", "id": str(offer.id)}), 201

    except (KeyError) as e:
        return jsonify({"error": str(e)}), 400


def filter_entity(field, value):
    """
    Filter by related entity.
    """

    result = Offer.objects.filter(**{field: value})
    if not result:
        log_resource_not_found("Offer", f"{field}", value)
        return jsonify({"error": f"No offers found for {field} = {value}"}), 404
    return format_offers_response(result)

def get_entity(model, value):
    """
    Get an entity by value.
    """
    try:
        return model.objects.get(id=value)
    except model.DoesNotExist:
        log_resource_not_found(f"{model.__name__}", "_id", value)
        raise None


def pagination_config(base_queryset):
    page = request.args.get("page", 1, type=int)
    pagesize = request.args.get("pagesize", 10, type=int)
    skip = (page - 1) * pagesize

    result = base_queryset.skip(skip).limit(pagesize)

    return result, page, pagesize


def format_offers_response(base_queryset):
    total_count = base_queryset.count()

    result, page, pagesize = pagination_config(base_queryset)

    response_data = [
        {
            "id": str(r.id),
            "discipline": r.discipline,
            "period": r.period,
            "campus": r.campus,
            "room": r.room,
            "teacher": r.teacher,
            "total_enrolled": r.total_enrolled,
            "total_optatives_enrolled": r.total_optatives_enrolled,
            "year": r.year,
            "semester": r.semester,
            "offer_id": r.offer_id,
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

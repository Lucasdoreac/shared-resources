from flasgger import swag_from
from flask import Blueprint, jsonify, request
from utils.cache import cache
from DAL import Type
from utils import log_info_request, log_resource_not_found, get_swagger_specification

types_bp = Blueprint('types_bp', __name__, url_prefix="/types")

spec = get_swagger_specification(path="types", method="GET")
@types_bp.route("/", methods=["GET"])
@log_info_request
@swag_from(spec)
@cache.cached(timeout=43200, query_string=True)  # Cache for 12 hours
def get_types():
    type_id = request.args.get("type_id")
    if type_id:
        try:
            return get_type_by_id(type_id)
        except Type.DoesNotExist:
            log_resource_not_found("Type", "type_id", type_id)
            return jsonify({"error": "TypeNotFound"}), 404

    collection_name = request.args.get("collection_name")
    type_name = request.args.get("type_name")
    if collection_name or type_name:
        result = get_type_by_name(collection_name, type_name)
        if result:
            return result

    types = Type.objects.all()
    return format_type_response(types)

def get_type_by_id(type_id):
    doc = Type.objects.get(id=type_id)
    if doc:
        return jsonify({
            "id": doc.id,
            "types": [
                {
                    "id": d.id,
                    "type": d.type,
                    "name": d.name
                } for d in doc.types
            ],
            "collection": doc.collection
        })


def get_type_by_name(collection_name, type_name):
    if collection_name and not type_name:
        return filter_by_collection_name(collection_name)


    if type_name and not collection_name:
        return filter_by_type_name(type_name)

    return None


def filter_by_collection_name(collection_name):
    docs = Type.objects.filter(collection__icontains=collection_name)
    if not docs:
        return jsonify({"error": "NotFound"}), 404
    return format_type_response(docs)

def filter_by_type_name(type_name):
    docs = Type.objects.filter(types__name__icontains=type_name)
    if not docs:
        return jsonify({"error": "NotFound"}), 404

    response = []
    for d in docs:
        matched_subdocs = [
            {
                "id": detail.id,
                "type": detail.type,
                "nome": detail.name
            }
            for detail in d.types
            if type_name.lower() in detail.name.lower()
        ]

        if matched_subdocs:
            response.append({
                "id": d.id,
                "types": matched_subdocs,
                "collection": d.collection
            })

    if not response:
        return jsonify({"error": "NotFound"}), 404

    return jsonify(response)

def format_type_response(types):
    return jsonify([
        {
            "id": t.id,
            "types": [
                {
                    "id": detail.id,
                    "type": detail.type,
                    "name": detail.name
                } for detail in t.types
            ],
            "collection": t.collection
        }
        for t in types
    ])

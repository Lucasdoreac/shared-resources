import requests
from flask import Blueprint, jsonify, request
import datetime
from utils.cache import cache
from BLL.schema import DeactivateTeacher
from DAL import Offer, Campus, Discipline, Period, Room, Teacher
from utils import log_info_request, log_resource_not_found, check_api_key, get_swagger_specification

deactivate_teacher_bp = Blueprint('deactivate_teacher_bp', __name__, url_prefix="/softdel")


@deactivate_teacher_bp.route("/", methods=["DELETE"])
@cache.cached(timeout=43200, query_string=True)
def delete_item():
    teacher_name = request.args.get("teacher_name")
    mutation = f'''
    mutation {{
  deactivateTeacher(name:{teacher_name}) {{   
    teacher {{
      id
      name

    }}
  }}
}} '''

    mutresponse = (requests.post("http://127.0.0.1:5081/graphql", json={"query": mutation}))

    if mutresponse.status_code == 200:

        return jsonify(mutresponse.json()), 200
    else:
        return jsonify({"error": "Erro ao executar mutation"}), 500
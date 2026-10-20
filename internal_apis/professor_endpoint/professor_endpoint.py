from flask import Blueprint, jsonify, request

from BLL.teacher_service import (
    AmbiguousTeacherName, TeacherNotFound, deactivate_teacher_by_name,
)
from utils import check_api_key, log_resource_not_found

deactivate_teacher_bp = Blueprint('deactivate_teacher_bp', __name__, url_prefix="teachers/softdel")


@deactivate_teacher_bp.route("/", methods=["DELETE"])
@check_api_key
def delete_item():
    """Desativa o professor de nome exato `teacher_name` (mesma regra da mutation GraphQL)."""
    teacher_name = request.args.get("teacher_name")
    if not teacher_name:
        return jsonify({"error": "teacher_name is required"}), 400
    try:
        teacher = deactivate_teacher_by_name(teacher_name)
    except TeacherNotFound:
        log_resource_not_found("Teacher", "teacher_name", teacher_name)
        return jsonify({"error": "Teacher not found"}), 404
    except AmbiguousTeacherName:
        return jsonify({"error": "More than one teacher has this name"}), 409
    return jsonify({
        "id": teacher.id,
        "name": teacher.name,
        "active": teacher.active,
        "soft_deleted": teacher.soft_deleted,
    }), 200

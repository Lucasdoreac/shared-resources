"""Regra de negócio única da desativação de professor (REST e GraphQL)."""
import datetime

from DAL import Teacher
from utils.cache import cache


class TeacherNotFound(Exception):
    pass


class AmbiguousTeacherName(Exception):
    pass


def active_teachers():
    """Professores visíveis nas listagens: `soft_deleted` vazio ou ausente (documentos legados)."""
    return Teacher.objects(soft_deleted=None)


def deactivate_teacher_by_name(name):
    """Desativa o professor cujo nome é exatamente `name` e devolve o documento recarregado.

    `soft_deleted` (timestamp UTC) é a fonte de verdade; `active=False` é gravado junto.
    Idempotente: se já estiver desativado, o timestamp original é preservado.
    """
    matches = list(Teacher.objects(name=name).limit(2))
    if not matches:
        raise TeacherNotFound(name)
    if len(matches) > 1:
        raise AmbiguousTeacherName(name)

    teacher = matches[0]
    if not teacher.soft_deleted:
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        teacher.update(set__soft_deleted=timestamp, set__active=False)
        cache.clear()  # listagens de professores são cacheadas por 12 h
    teacher.reload()
    return teacher

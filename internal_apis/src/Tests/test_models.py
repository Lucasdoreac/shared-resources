import pytest
import mongomock
from mongoengine import connect, disconnect
from DAL.models import Campus, Course, Discipline, Teacher


# Function-scoped (não module-scoped) e sempre desconectando no teardown:
# antes, essa fixture era scope="module" e nunca chamava disconnect(), então
# a conexão mongomock ficava "vazando" pros testes de outros arquivos que
# rodassem depois na mesma sessão do pytest (ex.: test_loaders.py), que
# então tentavam connect() de novo com parâmetros diferentes pro mesmo
# alias "default" e estouravam ConnectionError.
@pytest.fixture
def mongo_connection():
    disconnect()
    connect(db="test_db", host="localhost", mongo_client_class=mongomock.MongoClient)
    yield
    disconnect()


def test_campus_creation(mongo_connection):
    # Campos atuais do modelo (DAL/models.py): id (PK) e name -- não
    # campus_id/campus, que nunca existiram neste repo (models.py só tem um
    # commit desde que foi criado, já com os nomes atuais).
    campus = Campus(id="1", name="Main Campus")
    campus.save()

    saved_campus = Campus.objects(id="1").first()

    assert saved_campus is not None
    assert saved_campus.name == "Main Campus"


def test_course_creation(mongo_connection):
    # Course exige code (required=True) além de id/name/coordinator.
    course = Course(id=101, code="CS101", name="Computer Science")
    course.save()

    saved_course = Course.objects(id=101).first()

    assert saved_course is not None
    assert saved_course.name == "Computer Science"
    assert saved_course.code == "CS101"


def test_discipline_creation(mongo_connection):
    # Discipline.course é ListField(IntField()): uma lista de ids de curso,
    # não uma referência a um documento Course (o modelo atual não usa
    # ReferenceField aqui -- a resolução por id é feita via DataLoader em
    # BLL/loaders.py, não pelo mongoengine).
    course = Course(id=1, code="MAT101", name="Mathematics")
    course.save()

    discipline = Discipline(
        id=101,
        name="Calculus",
        course=[course.id],
        workload=60
    )
    discipline.save()

    saved_discipline = Discipline.objects.get(id=101)

    assert saved_discipline.name == "Calculus"
    assert saved_discipline.course == [1]
    assert saved_discipline.workload == 60


def test_teacher_creation(mongo_connection):
    # Teacher.course é ListField(IntField()) -- mesma observação acima.
    Course(id=54, code="CS101", name="Computer Science").save()
    Course(id=1, code="GAM101", name="Games").save()

    teacher = Teacher(
        id="T01",
        name="Dr. Smith",
        course=[54, 1],
        email="dr.smith@udf.edu.br",
    )
    teacher.save()

    saved_teacher = Teacher.objects(id="T01").first()

    assert saved_teacher is not None
    assert saved_teacher.name == "Dr. Smith"
    assert saved_teacher.course == [54, 1]
    assert saved_teacher.email == "dr.smith@udf.edu.br"

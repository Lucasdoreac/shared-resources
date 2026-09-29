import pytest
import mongomock
from mongoengine import connect, disconnect
from DAL.models import Campus, Course, Discipline, Teacher

@pytest.fixture
def mongo_connection():
    disconnect()
    connection = connect(
        db="test_db", host="localhost", mongo_client_class=mongomock.MongoClient
    )
    connection.drop_database("test_db")
    yield
    disconnect()

def test_campus_creation(mongo_connection):
    # Arrange
    campus = Campus(id="1", name="Main Campus")
    campus.save()

    # Act
    saved_campus = Campus.objects(id="1").first()

    # Assert
    assert saved_campus is not None
    assert saved_campus.name == "Main Campus"

def test_course_creation(mongo_connection):
    # Arrange
    course = Course(id=101, code="CS101", name="Computer Science")
    course.save()

    # Act
    saved_course = Course.objects(id=101).first()

    # Assert
    assert saved_course is not None
    assert saved_course.name == "Computer Science"

def test_discipline_creation(mongo_connection):
    # Arrange
    course = Course(id=1, code="MATH", name="Mathematics")
    course.save()

    discipline = Discipline(
        id=101,
        name="Calculus",
        course=[course.id],
        workload=60,
    )
    discipline.save()

    # Act
    saved_discipline = Discipline.objects.get(id=101)

    # Assert
    assert saved_discipline.name == "Calculus"
    assert saved_discipline.course == [course.id]
    assert saved_discipline.workload == 60


def test_teacher_creation(mongo_connection):
    # Arrange
    computer_course = Course(id=54, code="CS54", name="Computer Science")
    computer_course.save()

    games_course = Course(id=1, code="GAMES", name="Games")
    games_course.save()

    teacher = Teacher(
        id="T01",
        name="Dr. Smith",
        course=[computer_course.id, games_course.id],
    )
    teacher.save()

    # Act
    saved_teacher = Teacher.objects(id="T01").first()

    # Assert
    assert saved_teacher is not None
    assert saved_teacher.name == "Dr. Smith"
    assert saved_teacher.course == [54, 1]

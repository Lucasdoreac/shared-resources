import pytest
import mongomock
from mongoengine import connect, disconnect
from DAL.models import Campus, Course, Discipline, Teacher

@pytest.fixture(scope="module")
def mongo_connection():
    disconnect()
    connect(db="test_db", host="localhost", mongo_client_class=mongomock.MongoClient)
    yield

def test_campus_creation(mongo_connection):
    # Arrange
    campus = Campus(campus_id="1", campus="Main Campus")
    campus.save()

    # Act
    saved_campus = Campus.objects(campus_id="1").first()

    # Assert
    assert saved_campus is not None
    assert saved_campus.name == "Main Campus"

def test_course_creation(mongo_connection):
    # Arrange
    course = Course(course_id=101, course="Computer Science")
    course.save()

    # Act
    saved_course = Course.objects(course_id=101).first()

    # Assert
    assert saved_course is not None
    assert saved_course.name == "Computer Science"

def test_discipline_creation(mongo_connection):
    # Arrange
    course = Course(course_id=1, course="Mathematics")
    course.save()

    discipline = Discipline(
        discipline_id=101,
        discipline="Calculus",
        course_id=course,
        workload=60
    )
    discipline.save()

    # Act
    saved_discipline = Discipline.objects.get(discipline_id=101)

    # Assert
    assert saved_discipline.name.name == "Mathematics"
    assert saved_discipline.workload == 60


def test_teacher_creation(mongo_connection):
    # Arrange
    computer_course = Course(course_id=54, course="Computer Science")
    computer_course.save()

    games_course = Course(course_id=1, course="Games")
    games_course.save()

    teacher = Teacher(teacher_id="T01", teacher="Dr. Smith", courses=[
        Course(course_id=54, course="Computer Science"),
        Course(course_id=1, course="Games")
    ])
    teacher.save()

    # Act
    saved_teacher = Teacher.objects(teacher_id="T01").first()

    # Assert
    assert saved_teacher is not None
    assert saved_teacher.teacher == "Dr. Smith"
    assert len(saved_teacher.courses) > 1
    assert saved_teacher.courses[0].name == "Computer Science"
    assert saved_teacher.courses[1].name == "Games"


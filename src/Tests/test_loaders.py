import pytest
import mongomock
from mongoengine import disconnect, connect

from DAL import models
from BLL import loaders


@pytest.fixture(scope="function")
def mongo_connection():
    connect(db="test_db", host="mongodb://localhost", alias="default", mongo_client_class=mongomock.MongoClient)
    yield
    disconnect()

@pytest.fixture
def mock_courses(mongo_connection):
    courses = [
        models.Course(id=1, name="Engenharia de Software"),
        models.Course(id=2, name="Ciência da Computação"),
        models.Course(id=3, name="Sistemas Operacionais"),
    ]


    for course in courses:
        course.save()

    return courses


def test_course_loader(mock_courses):
    # Arrange
    loader = loaders.ContextLoaders()
    course_loader = loader.course_loader.course_batch

    # Act
    courses_ids = [1, 2, 3]
    result = course_loader.load_many(courses_ids).get()

    # Assert
    assert result == mock_courses



# tests/test_dal.py
import mongomock
import pytest
from bson import json_util
# Mocking pymongo.MongoClient with mongomock.MongoClient globally before importing any modules.
# This ensures that any use of MongoClient in the imported modules will automatically use the mocked version.
# It is essential to perform this mock before imports to prevent any real database connections
# from being established during module initialization, which can occur if MongoClient is instantiated
# at the module level or within class definitions. This approach ensures all database interactions
# are mocked, providing a consistent, isolated testing environment without side effects.
pytest.MonkeyPatch().setattr('pymongo.MongoClient', mongomock.MongoClient)
from src.DAL import MongoDBConnectionFactory


class TestMongoDBConnectionFactory:

    @pytest.fixture(autouse=True)
    def set_client(self):
        MongoDBConnectionFactory.init_app("mongodb://localhost:27017/", "test_db")

    def test_singleton_client_instance(self):
        """Test that the MongoDBConnectionFactory returns the same client instance."""
        client1 = MongoDBConnectionFactory.get_db().client
        client2 = MongoDBConnectionFactory.get_db().client
        assert client1 is client2, "MongoDBConnectionFactory should return the same MongoClient instance."

    def test_database_access(self):
        """Test that the MongoDBConnectionFactory returns a valid database instance."""
        db = MongoDBConnectionFactory.get_db()
        assert db.name == 'test_db', f"Should access the correct database."

    def test_data_retrieval(self):
        """Test retrieving data from a known collection."""
        db = MongoDBConnectionFactory.get_db()
        db['test_collection'].insert_one({'name': 'test_item'})
        count = db['test_collection'].count_documents({})
        assert count == 1, "Should retrieve data from 'test_collection'."

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Reset the client after each test to avoid shared state between tests
        yield
        MongoDBConnectionFactory._client = None

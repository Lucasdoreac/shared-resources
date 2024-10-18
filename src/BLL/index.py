from flask import jsonify

from src.DAL import *

# Initialize repository instances
buildings_repository = BuildingsRepository()
rooms_repository = RoomsRepository()
types_repository = TypesRepository()


class FlowController:

    @staticmethod
    def find_all_buildings():
        return buildings_repository.find_all()

    @staticmethod
    def find_all_rooms():
        return rooms_repository.find_all()

    @staticmethod
    def find_all_types():
        return types_repository.find_all()

    def find_type_by_collection(collection: str):
        type_data = types_repository.get_type_by_collection(collection)
        if type_data:
            return jsonify(type_data), 200
        else:
            return jsonify({'error': 'There is no such type'}), 404



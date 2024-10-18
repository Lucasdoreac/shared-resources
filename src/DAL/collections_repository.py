from datetime import datetime, timedelta
from .base_repository import BaseRepository


class BuildingsRepository(BaseRepository):
    def get_collection_name(self):
        return self.db["buildings"]


class RoomsRepository(BaseRepository):
    def get_collection_name(self):
        return self.db.rooms


class TypesRepository(BaseRepository):
    def get_collection_name(self):
        return self.db.types

    def get_type_by_collection(self, collection_name):
        return self.convert_id(list(self.types_collection.find({"collection": collection_name})))





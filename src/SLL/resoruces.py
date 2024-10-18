from graphene import ObjectType, String, Int, List

from src.BLL import FlowController


class RoomType(ObjectType):
    room_id = String()
    name = String()
    students_capacity = Int()
    building_id = String()
    room_number = String()
    floor = String()


class BuildingType(ObjectType):
    building_id = String()
    address = String()
    acronym = String()
    close_at = String()
    open_at = String()
    maps_link = String()


class TypeEntry(ObjectType):
    id = Int()
    type = String()


class TypesType(ObjectType):
    types_id = String()
    collection = String()
    types = List(TypeEntry)


class Query(ObjectType):
    rooms = List(RoomType)
    buildings = List(BuildingType)
    types = List(TypesType)

    def resolve_rooms(self, info):
        rooms_data = FlowController.find_all_rooms()
        return [
            {
                "room_id": room["_id"],
                "name": room.get("name"),
                "students_capacity": room.get("studentsCapacity"),
                "building_id": room.get("buildingId"),
                "room_number": room.get("roomNumber", ""),
                "floor": room.get("floor", "")
            }
            for room in rooms_data
        ]

    def resolve_buildings(self, info):
        buildings_data = FlowController.find_all_buildings()
        return [
            {
                "building_id": building["_id"],
                "address": building.get("address"),
                "acronym": building.get("acronym"),
                "close_at": building.get("closeAt"),
                "open_at": building.get("openAt"),
                "maps_link": building.get("mapsLink")
            }
            for building in buildings_data
        ]

    def resolve_types(self, info):
        types_data = FlowController.find_all_types()
        return [
            {
                "types_id": types_entry["_id"],
                "collection": types_entry.get("collection"),
                "types": [
                    {"id": type_item["id"], "type": type_item["type"]}
                    for type_item in types_entry.get("types", [])
                ]
            }
            for types_entry in types_data
        ]


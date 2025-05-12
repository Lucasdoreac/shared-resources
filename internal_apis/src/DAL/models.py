from graphene import Boolean
from mongoengine import Document, StringField, IntField, ListField, EmbeddedDocumentField, EmbeddedDocument, \
    BooleanField


class Campus(Document):
    """Campus entity model"""
    meta = {"collection": "campus"}
    id = StringField(primary_key=True, db_field='_id')
    name = StringField(required=True, db_field='CAMPUS')


class Course(Document):
    """Course entity model"""
    meta = {"collection": "courses"}
    id = IntField(primary_key=True, db_field='_id')
    code = StringField(required=True, db_field='COD_CURS')
    name = StringField(required=True, db_field='DES_CURS')
    coordinator = StringField(required=False, db_field='COORDINATOR')


class Discipline(Document):
    """Discipline entity model"""
    meta = {"collection": "disciplines"}
    id = IntField(primary_key=True,  db_field='_id')
    name = StringField(required=True, db_field='DES_DISC')
    course = ListField(IntField(), required=True, db_field='COD_CURS')
    workload = IntField(min_value=20, required=True, db_field='CARG_HOR')


class Period(Document):
    """Period entity model"""
    meta = {"collection": "periods"}
    id = StringField(primary_key=True, db_field='_id')
    name = StringField(required=True, db_field='PERIODO')


class Room(Document):
    """Room entity model"""
    meta = {"collection": "rooms"}
    id = StringField(primary_key=True, db_field='_id')
    name = StringField(required=True, db_field='NR_SALA')
    campus = StringField(required=True, db_field='CAMPUS')


class Teacher(Document):
    """Teacher entity model"""
    meta = {"collection": "teachers"}
    id = StringField(primary_key=True, db_field='_id')
    name = StringField(required=True, db_field='PROFESSOR')
    course = ListField(IntField(), required=True, db_field='COD_CURS')
    email = StringField(required=False, db_field='email')
    active = BooleanField(required=True, db_field='ACTIVE')
    soft_deleted = StringField(required=False, db_field='soft_deleted')


class Offer(Document):
    """Offer entity model"""
    meta = {"collection": "offers"}
    discipline = IntField(required=True, db_field='COD_DISC')
    period = StringField(required=True, db_field='period_id')
    campus = StringField(required=True, db_field='campus_id')
    room = StringField(required=True, db_field='room_id')
    teacher = StringField(required=True, db_field='teacher_id')
    total_enrolled = IntField(required=True, db_field='TOT_MAT')
    total_optatives_enrolled = IntField(required=True, db_field='TOT_MAT_OPT')
    year = IntField(required=True, db_field='ANO')
    semester = IntField(required=True, db_field='SEMESTRE')
    offer_id = IntField(required=True, db_field='ID_OFERT')


    def fetch_entity(loader, model, identifier, name_field="name"):
        """
        Search an entity using DataLoader and fallback to MongoEngine

        :param loader: Loads an entity by ID using DataLoader.
        :param model: MongoEngine Model associated.
        :param identifier: Entity identifier (ID or name).
        :param name_field: Model's field (default: "name").

        :return: The retrieved entity (instance of 'model').

        :raises ValueError: If the entity cannot be found by either the loader or direct query.

        """

        entity = loader.load(identifier).get()
        if entity:
            return entity

        query = {f"{name_field}__icontains": identifier}
        entity = model.objects(**query).first()
        if not entity:
            raise ValueError(f"{model.__name__} '{identifier}' not found")

        return entity


class TypeDetail(EmbeddedDocument):
    """Subdocument for individual type details"""
    id = IntField(required=True)
    name = StringField(required=True)
    type = StringField(required=True)

class Type(Document):
    """Type entity model"""
    meta = {"collection": "types"}
    id = IntField(primary_key=True, db_field='_id')
    types = ListField(EmbeddedDocumentField(TypeDetail), required=True, db_field='types')
    collection = StringField(required=True, db_field='collection')



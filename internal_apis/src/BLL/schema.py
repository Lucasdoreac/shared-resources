"""
This module defines a GraphQL schema for querying and mutating data related to a university-like environment. 
It uses MongoEngine models to represent entities such as Campuses, Courses, Disciplines, Periods, Rooms, Teachers, Offers, and Types. 
The schema includes queries for fetching lists of these entities and various search parameters. 
It also provides mutations for creating Offers.

This schema leverages DataLoader-like loaders (through `info.context['loaders']`) to batch load related entities 
(e.g., courses associated with a discipline, or the campus associated with a room), improving query efficiency.

Classes ending with `Type` are GraphQL object types corresponding to MongoEngine models or derived objects.
The `Query` class specifies root-level queries. The `Mutation` class defines root-level mutations, such as `create_offer`.
"""

import graphene
from graphene import ObjectType, List, Field, Mutation, Scalar
from graphene_mongo import MongoengineObjectType
import datetime

from DAL import Campus, Course, Discipline, Period, Room, Teacher, Offer, Type


class CampusType(MongoengineObjectType):
    """
    GraphQL object type representing a Campus.

    Fields:
        id (Int): The unique ID of the campus.
        name (String): The name of the campus.
        Additional fields come directly from the `Campus` model.
    """

    class Meta:
        model = Campus


class CourseType(MongoengineObjectType):
    """
    GraphQL object type representing a Course.

    Fields:
        id (Int): The unique ID of the course.
        name (String): The name of the course.
        Additional fields come directly from the `Course` model.
    """

    class Meta:
        model = Course


class DisciplineType(MongoengineObjectType):
    """
    GraphQL object type representing a Discipline.

    Fields:
        id (Int): The unique ID of the discipline.
        name (String): The name of the discipline.
        course (List[CourseType]): A list of courses associated with this discipline.
        Additional fields come directly from the `Discipline` model.
    """
    course = List(CourseType)

    class Meta:
        model = Discipline

    def resolve_course(root, info):
        """
        Resolve the list of associated courses for this discipline using a DataLoader.
        """
        course_loader = info.context['loaders']['context-loader'].course_loader.course_batch
        return course_loader.load_many(root.course)


class PeriodType(MongoengineObjectType):
    """
    GraphQL object type representing a Period.

    Fields:
        id (Int): The unique ID of the period.
        name (String): The name of the period.
        Additional fields come directly from the `Period` model.
    """

    class Meta:
        model = Period


class RoomType(MongoengineObjectType):
    """
    GraphQL object type representing a Room.

    Fields:
        id (Int): The unique ID of the room.
        name (String): The name of the room.
        campus (CampusType): The campus associated with this room.
        Additional fields come directly from the `Room` model.
    """
    campus = Field(CampusType)

    class Meta:
        model = Room

    def resolve_campus(root, info):
        """
        Resolve the campus for this room by querying the database.
        """
        campus = Campus.objects(name=root.campus).first()
        return campus


class TeacherType(MongoengineObjectType):
    """
    GraphQL object type representing a Teacher.

    Fields:
        id (Int): The unique ID of the teacher.
        name (String): The name of the teacher.
        course (List[CourseType]): The courses associated with this teacher.
        Additional fields come directly from the `Teacher` model.
    """
    course = List(CourseType)

    class Meta:
        model = Teacher

    def resolve_course(root, info):
        """
        Resolve the list of courses taught by this teacher using a DataLoader.
        """
        course_loader = info.context['loaders']['context-loader'].course_loader.course_batch
        return course_loader.load_many(root.course)


class TypesDetailType(graphene.ObjectType):
    """
    Auxiliary GraphQL object type representing detailed information about a type entry.

    Fields:
        id (Int): The unique ID of the type detail.
        name (String): The name associated with this type detail.
        type (String): A string descriptor for this type detail category.
    """
    id = graphene.Int(required=True)
    name = graphene.String()
    type = graphene.String(required=True)


class TypesType(MongoengineObjectType):
    """
    GraphQL object type representing a Type, which aggregates a list of TypesDetail entries.

    Fields:
        id (Int): The unique ID of the type.
        name (String): The name of the type.
        types (List[TypesDetailType]): A list of detailed type objects.
        Additional fields come directly from the `Type` model.
    """
    types = List(TypesDetailType)

    class Meta:
        model = Type


class OfferType(MongoengineObjectType):
    """
    GraphQL object type representing an Offer, a combination of discipline, period, campus, room, and teacher.

    Fields:
        id (Int): The unique ID of the offer.
        discipline (DisciplineType): The associated discipline.
        period (PeriodType): The associated period.
        campus (CampusType): The associated campus.
        room (RoomType): The associated room.
        teacher (TeacherType): The associated teacher.
        total_enrolled (Int): The total number of enrolled students.
        Additional fields come directly from the `Offer` model.
    """
    discipline = Field(DisciplineType)
    period = Field(PeriodType)
    campus = Field(CampusType)
    room = Field(RoomType)
    teacher = Field(TeacherType)

    class Meta:
        model = Offer

    def resolve_discipline(root, info):
        """Resolve the discipline entity using a DataLoader."""
        loader = info.context['loaders']['context-loader'].offer_loader.discipline_batch
        return loader.load(root.discipline)

    def resolve_period(root, info):
        """Resolve the period entity using a DataLoader."""
        loader = info.context['loaders']['context-loader'].offer_loader.period_batch
        return loader.load(root.period)

    def resolve_campus(root, info):
        """Resolve the campus entity using a DataLoader."""
        loader = info.context['loaders']['context-loader'].offer_loader.campus_batch
        return loader.load(root.campus)

    def resolve_room(root, info):
        """Resolve the room entity using a DataLoader."""
        loader = info.context['loaders']['context-loader'].offer_loader.room_batch
        return loader.load(root.room)

    def resolve_teacher(root, info):
        """Resolve the teacher entity using a DataLoader."""
        loader = info.context['loaders']['context-loader'].offer_loader.teacher_batch
        return loader.load(root.teacher)


class Query(ObjectType):
    """
    The root Query object for the GraphQL schema.

    Provides various query fields to fetch lists of campuses, courses, disciplines, periods, rooms, teachers, offers, and types. 
    Includes search, pagination (first, skip), and filtering (by ID or name) capabilities.
    """

    campus = List(CampusType)
    courses = List(
        CourseType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
        course_id=graphene.Int(),
    )
    disciplines = List(
        DisciplineType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
        discipline_id=graphene.Int(),
        searchCourse=graphene.String(),
    )
    periods = List(PeriodType)
    rooms = List(
        RoomType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
        room_id=graphene.String(),
    )
    teachers = List(
        TeacherType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
        teacher_id=graphene.String(),
        searchCourse=graphene.String(),
    )
    offers = List(
        OfferType,
        first=graphene.Int(),
        skip=graphene.Int(),
        searchCampus=graphene.String(),
        searchDiscipline=graphene.String(),
        searchPeriod=graphene.String(),
        searchRoom=graphene.String(),
        searchTeacher=graphene.String(),
        searchOfferId=graphene.Int(),
        searchSemester=graphene.Int(),
        searchYear=graphene.Int(),
    )
    types = List(
        TypesType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
    )

    def resolve_campus(root, info):
        """Return all campuses."""
        return Campus.objects.all()

    def resolve_get_campus_by_id(root, info, id):
        """Return a single campus by its ID."""
        return Campus.objects.get(id=id)

    def resolve_courses(root, info, search=None, first=None, skip=None, course_id=None):
        """
        Return a list of courses. Supports filtering by name (search), limiting (first), 
        skipping (skip), and filtering by specific course_id.
        """
        query = Course.objects.filter(name__icontains=search) \
            if search else Course.objects.all()

        if first:
            query = query.limit(first)

        if skip:
            query = query.skip(skip)

        if course_id:
            query = query.filter(id=course_id)

        return query

    def resolve_disciplines(root, info, search=None, first=None, skip=None, discipline_id=None, searchCourse=None):
        """
        Return a list of disciplines. Supports filtering by name (search), limiting (first), 
        skipping (skip), filtering by discipline_id, and searching by associated course name (searchCourse).
        """
        query = Discipline.objects.filter(name__icontains=search) \
            if search else Discipline.objects.all()

        if first:
            query = query.limit(first)

        if skip:
            query = query.skip(skip)

        if discipline_id:
            query = query.filter(discipline_id=discipline_id)

        if searchCourse:
            course = Course.objects(name__icontains=searchCourse).first()
            if course:
                query = query.filter(course=course.id)
            else:
                return []

        return query

    def resolve_periods(root, info):
        """Return all periods."""
        return Period.objects.all()

    def resolve_rooms(root, info, search=None, first=None, skip=None, room_id=None):
        """
        Return a list of rooms. Supports filtering by name (search), limiting (first), 
        skipping (skip), and filtering by room_id.
        """
        query = Room.objects.filter(name__icontains=search) if search else Room.objects.all()

        if first:
            query = query.limit(first)

        if skip:
            query = query.skip(skip)

        if room_id:
            query = query.filter(id=room_id)

        return query

    def resolve_teachers(root, info, search=None, first=None, skip=None, teacher_id=None, searchCourse=None):
        """
        Return a list of teachers. Supports filtering by name (search), limiting (first), 
        skipping (skip), filtering by teacher_id, and searching by associated course name (searchCourse).
        """
        query = Teacher.objects.filter(name__icontains=search) if search else Teacher.objects.all()

        if first:
            query = query.limit(first)

        if skip:
            query = query.skip(skip)

        if teacher_id:
            query = query.filter(id=teacher_id)

        if searchCourse:
            course = Course.objects(name__icontains=searchCourse).first()
            if course:
                query = query.filter(course=course.id)
            else:
                return []

        return query

    def resolve_offers(
            root, info, first=None, skip=None,
            searchCampus=None, searchDiscipline=None,
            searchPeriod=None, searchRoom=None,
            searchTeacher=None, searchOfferId=None,
            searchSemester=None, searchYear=None
    ):
        """
        Return a list of offers. Supports filtering by related entities' names 
        (campus, discipline, period, room, teacher) and paging (first, skip).
        """
        query = Offer.objects.all()

        if first:
            query = query.limit(first)

        if skip:
            query = query.skip(skip)

        if searchCampus:
            campus = Campus.objects(name__icontains=searchCampus).first()
            if campus:
                query = query.filter(campus=campus.id)
            else:
                return []
        if searchDiscipline:
            discipline = Discipline.objects(name__icontains=searchDiscipline).first()
            if discipline:
                query = query.filter(discipline=discipline.id)
            else:
                return []
        if searchPeriod:
            period = Period.objects(name__icontains=searchPeriod).first()
            if period:
                query = query.filter(period=period.id)
            else:
                return []
        if searchRoom:
            room = Room.objects(name__icontains=searchRoom).first()
            if room:
                query = query.filter(room=room.id)
            else:
                return []
        if searchTeacher:
            teacher = Teacher.objects(name__icontains=searchTeacher).first()
            if teacher:
                query = query.filter(teacher=teacher.id)
            else:
                return []
        if searchOfferId:
            query = query.filter(offer_id=searchOfferId)
        if searchSemester:
            query = query.filter(semester=searchSemester)
        if searchYear:
            query = query.filter(year=searchYear)

        return query

    def resolve_types(root, info, search=None):
        query = Type.objects.filter(collection__icontains=search) \
            if search else Type.objects.all()
        return query


class IntOrString(Scalar):
    """
    A custom scalar that may represent either an Int or a String. 
    Useful in cases where an ID field might be numeric or a string.
    """

    @staticmethod
    def serialize(value):
        return value

    @staticmethod
    def parse_literal(node, _variables=None):  # graphene 3 passa as variáveis
        if node.value.isdigit():
            return int(node.value)
        return node.value

    @staticmethod
    def parse_value(value):
        try:
            return int(value)
        except ValueError:
            return value


class OfferInput(graphene.InputObjectType):
    """
    Input object type for creating an Offer mutation.

    Fields:
        discipline (IntOrString): The discipline ID (can be string or int).
        period (String): The period ID as a string.
        campus (String): The campus ID as a string.
        room (String): The room ID as a string.
        teacher (String): The teacher ID as a string.
        total_enrolled (Int): The total number of enrolled students.
        total_optatives_enrolled (Int): The total number of enrolled students in optative courses.
        offer_id (Int): The unique ID of the offer.
    """
    discipline = IntOrString(required=True)
    period = graphene.String(required=True)
    campus = graphene.String(required=True)
    room = graphene.String(required=True)
    teacher = graphene.String(required=True)
    total_enrolled = graphene.Int(required=True)

    ## add fields HERE
    total_optatives_enrolled = graphene.Int(required=True)
    year = graphene.Int(required=True)
    semester = graphene.Int(required=True)
    offer_id = graphene.Int(required=True)


class CreateOffer(Mutation):
    """
    Mutation for creating a new Offer.

    Arguments:
        offer_data (OfferInput): The input data required to create a new Offer.

    Returns:
        offer (OfferType): The newly created Offer object.
    """

    class Arguments:
        offer_data = graphene.Argument(OfferInput)

    offer = graphene.Field(OfferType)

    def mutate(self, info, offer_data):
        """
        Create and save a new Offer using the provided input. 
        Resolved entities (discipline, period, campus, room, teacher) are loaded from the DataLoader.
        """
        loader = info.context['loaders']['context-loader'].offer_loader

        discipline = Offer.fetch_entity(loader.discipline_batch, Discipline, offer_data.discipline)
        period = Offer.fetch_entity(loader.period_batch, Period, offer_data.period)
        campus = Offer.fetch_entity(loader.campus_batch, Campus, offer_data.campus)
        room = Offer.fetch_entity(loader.room_batch, Room, offer_data.room)
        teacher = Offer.fetch_entity(loader.teacher_batch, Teacher, offer_data.teacher)

        offer = Offer(
            discipline=discipline.id,
            period=period.id,
            campus=campus.id,
            room=room.id,
            teacher=teacher.id,
            total_enrolled=offer_data.total_enrolled,
            total_optatives_enrolled=offer_data.total_optatives_enrolled,
            year=datetime.datetime.now().year,
            semester=1 if datetime.datetime.now().month < 7 else 2,
            offer_id=offer_data.offer_id
        )
        offer.save()

        return CreateOffer(offer=offer)


class Mutation(ObjectType):
    """
    The root Mutation object for the GraphQL schema.

    Fields:
        create_offer (CreateOffer): Mutation to create a new Offer.
    """
    create_offer = CreateOffer.Field()

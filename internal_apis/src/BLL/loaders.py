from promise import Promise
from promise.dataloader import DataLoader
from DAL import Campus, Course, Discipline, Period, Room, Teacher, Offer

class BatchLoader(DataLoader):
    """
        A batch loader for efficiently loading model instances by their primary keys.

        This class inherits from `DataLoader` and is intended to be used for batching
        database fetch operations. Instead of performing a single query for each
        requested item, it fetches them all in a single query, thereby improving
        performance and reducing the number of database round trips.

        Attributes:
            model_class (models.Model): The Django model class this loader is responsible for.

        Methods:
            batch_load_fn(keys):
                Given a list of keys (usually primary keys), returns a `Promise` that resolves to
                the list of model instances corresponding to these keys.

            load_all():
                Returns a `Promise` that resolves to all instances of the `model_class`.
        """

    def __init__(self, model_class):
        """
        Initialize a BatchLoader instance for a specific model class.

        Args:
            model_class (models.Model): The Django model class to be loaded in batches.
        """
        super().__init__()
        self.model_class = model_class

    def batch_load_fn(self, keys):
        """

        Load multiple entities by their primary keys in a single database query.

        Args:
            keys (list): A list of primary key values for the entities to be loaded.

        Returns:
            Promise: A promise that resolves to a list of model instances in the same order
                     as the provided keys.
        """
        entities = self.model_class.objects.filter(id__in=keys)
        entity_map = {entity.id: entity for entity in entities}
        return Promise.resolve([entity_map.get(key) for key in keys])

    def load_all(self):
        """
        Load all instances of the `model_class`.

        Returns:
            Promise: A promise that resolves to a list of all model instances of `model_class`.
        """

        entities = self.model_class.objects.all()
        return Promise.resolve(entities)


class OfferLoader:
    """
    A loader container that provides batch loaders for offers and related models.

    This class holds references to several `BatchLoader` instances, each responsible
    for batching loads for a specific model type. It is used to gather related loaders
    in one place for convenience.

    Attributes:
        offer_batch (BatchLoader): A batch loader for Offer instances.
        discipline_batch (BatchLoader): A batch loader for Discipline instances.
        period_batch (BatchLoader): A batch loader for Period instances.
        campus_batch (BatchLoader): A batch loader for Campus instances.
        room_batch (BatchLoader): A batch loader for Room instances.
        teacher_batch (BatchLoader): A batch loader for Teacher instances.
    """
    def __init__(self):
        """
        Initialize the OfferLoader with batch loaders for all relevant models.
        """
        self.offer_batch = BatchLoader(Offer)
        self.discipline_batch = BatchLoader(Discipline)
        self.period_batch = BatchLoader(Period)
        self.campus_batch = BatchLoader(Campus)
        self.room_batch = BatchLoader(Room)
        self.teacher_batch = BatchLoader(Teacher)

class CourseLoader:
    """
    A loader container that provides batch loaders for course-related models.

    This class currently holds a reference to a batch loader for courses. It can be
    extended to include other related loaders if needed.

    Attributes:
        course_batch (BatchLoader): A batch loader for Course instances.
    """
    def __init__(self):
        """
        Initialize the CourseLoader with a batch loader for Course models.
        """
        self.course_batch = BatchLoader(Course)


class ContextLoaders:
    """
    A loader context that aggregates various loader groups.

    This class combines `OfferLoader` and `CourseLoader` into a single context,
    making it easier to access all the necessary batch loaders in one place.
    Typically, such a context is used in GraphQL or REST API views to efficiently
    fetch related data with fewer queries.

    Attributes:
        offer_loader (OfferLoader): The loader container for offer-related models.
        course_loader (CourseLoader): The loader container for course-related models.
    """
    def __init__(self):
        self.offer_loader = OfferLoader()
        self.course_loader = CourseLoader()
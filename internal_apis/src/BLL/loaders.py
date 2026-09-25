from DAL import Campus, Course, Discipline, Period, Room, Teacher, Offer


class BatchLoader:
    """Carregador por requisição, com cache por chave: cada entidade é buscada
    no banco no máximo uma vez por consulta GraphQL, e `load_many` busca as que
    faltam numa query só.

    Substitui o DataLoader do `promise` (graphene 2). No graphene 3 a execução
    é síncrona e os resolvers devolvem o valor direto, sem Promise.
    """

    def __init__(self, model_class):
        self.model_class = model_class
        self._cache = {}

    def load_many(self, keys):
        missing = [key for key in keys if key not in self._cache]
        if missing:
            found = {entity.id: entity for entity in self.model_class.objects.filter(id__in=missing)}
            for key in missing:
                self._cache[key] = found.get(key)
        return [self._cache[key] for key in keys]

    def load(self, key):
        return self.load_many([key])[0]

    def load_all(self):
        return list(self.model_class.objects.all())


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
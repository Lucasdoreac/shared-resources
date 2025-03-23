

# **GraphQL with MongoDB Project**

This project was developed to integrate **MongoDB** with **GraphQL**, using **Mongoengine** as the ORM for MongoDB. It
provides a robust API for manipulating data stored in the MongoDB database, structured to be scalable, maintainable,
and well-organized.

## **Overview**

The goal of this project is to expose data stored in MongoDB through a **GraphQL API**. We use **Mongoengine** to define
the models and perform queries on MongoDB. The GraphQL API allows interaction with the data using queries and resolvers
to efficiently return data.

### Access the GraphQL API and Rest API
- rest api link: http://localhost:5081/apidocs
- graphql api link: http://localhost:5081/graphql/graphiql

## **Project Structure**

The project is divided into three main components:

1. **Models** - Defines the data structure and collections in MongoDB.
2. **Schemas** - Maps models to GraphQL types, enabling data querying and manipulation via GraphQL.
3. **Queries** - Defines read operations and how the data is queried.

## **Models**

### **Main Responsibility**

**Models** are responsible for mapping MongoDB collections to Python documents. Each model is a class that inherits from
Mongoengine’s `Document`. The fields in the model correspond to the fields in the MongoDB collections.

### **Model Structure**

Each model should have a **`Meta` sub-class** that defines the collection name in MongoDB. By default, Mongoengine maps
the class name to the collection name, but using `meta = {"collection": "collection_name"}`, we can explicitly define
the collection name.

### **Model Example**
```python
class Campus(Document):
    meta = {"collection": "campus"}  # Collection name in MongoDB
    campus_id = StringField(primary_key=True)
    campus = StringField(required=True)
```

### **Role of Models**
- Define the structure of data in MongoDB.
- Map fields to corresponding data types (strings, integers, references, etc.).
- Determine MongoDB collections using the `meta` field.

## **Schemas**

### **Main Responsibility**

**Schemas** are responsible for mapping Mongoengine models to **GraphQL types**. They define how data is exposed to the
client via the GraphQL API and what types of data can be queried.

### **Schema Structure**

Inside each GraphQL type, there is a `Meta` sub-class that links the Mongoengine model to the GraphQL type. Defining
`model` in the `Meta` sub-class is essential to ensure that the GraphQL type knows which MongoDB model it represents.

### **Schema Example**
```python
class CampusGraphQLType(MongoengineObjectType):
    class Meta:
        model = models.Campus  # Links MongoDB model to GraphQL type
        interfaces = (Node,)  # Defines GraphQL type interfaces (e.g., Node)
```

### **Role of Schemas**
- Define how data is exposed via GraphQL.
- Map GraphQL types to Mongoengine models.
- Enable GraphQL queries to access data from the database.

## **Queries**

### **Main Responsibility**

**Queries** define the **read operations** that can be performed via GraphQL. Each query defines a field that represents
a data type or operation. The resolver function associated with each field determines how the data will be fetched from
the database and returned to the client.

### **Query Structure**

The **`Query`** class defines the fields that can be queried and the resolvers responsible for returning the data.
Resolvers query the database and return the data to the client. Queries can include simple operations, like fetching all
documents from a collection, or more complex operations with filters and sorting.

### **Query Example**
```python
class Query(ObjectType):
    all_campus = List(CampusGraphQLType)  # Field that returns a list of Campus

    def resolve_all_campus(self, info):
        return models.Campus.objects.all()  # Queries the data in MongoDB
```

### **Role of Queries**
- Define how data can be accessed via GraphQL.
- Map fields to resolver functions that access data from the database.
- Return the requested data through GraphQL queries.

## **How the Data Flow Works**

1. **Models**: These are representations of collections in MongoDB. They define the fields and data structure.
2. **Schemas**: These are the GraphQL types that define how data is exposed and accessed. Each data type is linked to a MongoDB model via the `Meta` sub-class.
3. **Queries**: These are responsible for accessing the data. They define how data can be queried and returned, mapping read operations to resolver functions.

## **Key Concepts**

- **References**: When a field in a document references another document, we use **ReferenceField** to create this relationship.
- **Field Resolution**: In the query, each field must have an associated resolver function that will fetch data from the database and return it as requested.
- **Meta Subclass**: In **Schemas** and **Models**, the `Meta` sub-class is crucial for configuring the link between the database and GraphQL.

## **Query Flow Example**

1. The client sends a GraphQL query, such as:
   ```graphql
   {
       allCampus {
           campus
       }
   }
   ```

2. The corresponding **Query** resolves the query, accessing the MongoDB database, using the appropriate **model**, and
3. returning the data.

3. The **Schema** transforms the returned data into a structure compatible with GraphQL and sends it back to the client.


## **DataLoader, GraphQL Context, and ContextLoader**

### **What is a DataLoader?**

The **DataLoader** is a utility used to batch and cache database queries efficiently. It is particularly useful in GraphQL to avoid the "N+1 query problem," where a resolver might execute a separate database query for every single node in a query tree, leading to poor performance.

### **How the DataLoader Works**

1. **Batching**: Instead of executing individual queries for each item, the DataLoader collects all requested keys during a single execution loop and fetches them in a single database query.
2. **Caching**: DataLoader caches results for the duration of a request to ensure that repeated requests for the same data don't trigger additional database queries.

### **DataLoader in This Project**

In this project, the `BatchLoader` class is used to implement the DataLoader functionality for MongoDB collections. Each `BatchLoader` is initialized with a specific model class and performs batched queries using the `batch_load_fn` method.

#### **BatchLoader Example**
```python
class BatchLoader(DataLoader):
    def __init__(self, model_class):
        super().__init__()
        self.model_class = model_class

    def batch_load_fn(self, keys):
        # Query the database for all requested keys in a single query
        entities = self.model_class.objects.filter(id__in=keys)
        entity_map = {entity.id: entity for entity in entities}
        # Return results in the same order as the requested keys
        return Promise.resolve([entity_map.get(key) for key in keys])
```

This `BatchLoader` ensures that all keys requested during a single query execution are fetched in a single database call, improving performance significantly.

---

### **What is the GraphQL Context?**

The **GraphQL context** is a shared object passed to every resolver during the execution of a GraphQL query. It serves as a container for shared resources like the database connection, authentication tokens, and, in this case, the DataLoader instances.

### **Using Context in This Project**

In this project, the context is used to provide access to the DataLoaders through the `ContextLoaders` class. This ensures that all resolvers in the GraphQL API can use the appropriate DataLoader for their needs.

---

### **What is ContextLoader?**

The `ContextLoaders` class centralizes the initialization of all DataLoader instances required by the API. It provides loaders for specific entities like `Offer` and `Course` to batch and cache database queries efficiently.

#### **ContextLoader Example**
```python
class ContextLoaders:
    def __init__(self):
        self.offer_loader = OfferLoader()
        self.course_loader = CourseLoader()
```

### **How ContextLoader Integrates with the Project**

1. **Centralized Loader Management**: All DataLoaders for the project are managed in one place, making it easier to maintain and expand.
2. **Efficient Query Resolution**: Resolvers use the loaders in `ContextLoaders` to batch and cache queries, improving performance.
3. **Integration with GraphQL Context**: The `ContextLoaders` instance is passed into the GraphQL context at the beginning of each request.

---

### **Resolvers Using DataLoader**

Resolvers in this project leverage the loaders from the context to handle database queries efficiently.

#### **Resolver Example**
Here’s an example of a resolver for the `DisciplineType` GraphQL type:
```python
class DisciplineType(MongoengineObjectType):
    course = List(CourseType)

    class Meta:
        model = models.Discipline

    def resolve_course(root, info):
        # Access the course_loader from the context
        course_loader = info.context['loaders'].course_loader.course_loader
        # Use load_many for batch fetching
        return course_loader.load_many(root.course)
```

- The resolver retrieves the `course_loader` from the GraphQL context, ensuring that all requested courses are fetched in a single database query.
- This reduces redundant queries and ensures scalability.

---

### **GraphQL Context Configuration**

The `ContextLoaders` instance is passed into the GraphQL context during request initialization in `app.py`:

#### **Context Setup in app.py**
```python
def graphql():
    data = request.get_json()
    context = {
        "loaders": ContextLoaders()  # Provide DataLoaders in the context
    }
    result = schema.execute(
        data.get("query"),
        variables=data.get("variables"),
        context_value=context,
    )
    return jsonify(result.data)
```

This setup ensures that every resolver can access the appropriate DataLoader during query execution.

---

### **Benefits of Using DataLoader and ContextLoader**

1. **Improved Performance**:
   - Queries are batched and executed as a single database call instead of multiple individual queries.
   - Repeated queries for the same data within the same request are cached, avoiding redundant database calls.

2. **Simplified Resolver Logic**:
   - Resolvers only need to specify the loader and the keys to fetch, simplifying the code.

3. **Scalability**:
   - As the data grows and queries become more complex, the use of DataLoader ensures the API remains performant.

---

### **Example Query Flow with DataLoader**

Here’s an example query and how it leverages the DataLoader:

#### Query
```graphql
{
    disciplines {
        course {
            id
            name
        }
    }
}
```

#### Execution Flow
1. **Resolver Execution**: The `resolve_course` function in `DisciplineType` retrieves the course IDs from the discipline data.
2. **DataLoader Fetching**: The `course_loader` batches all requested course IDs and fetches them in a single database query.
3. **Cache Check**: If a course has already been fetched within the same request, it is returned from the cache instead of querying the database again.
4. **Data Return**: The fetched courses are returned to the client in the requested structure.

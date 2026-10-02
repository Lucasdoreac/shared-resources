# GraphQL API Instructions

This document provides steps to run the `graphql_api.py` file and use the GraphQL API to query collections, both with and without search parameters.

## Prerequisites

Ensure you have [Poetry](https://python-poetry.org/docs/) installed.

### Step 1: Install Packages

To install the necessary dependencies using Poetry, follow these steps:

1. Open a terminal in the project directory.
2. Run the following command to install all required packages:

   ```bash
   poetry install
   ```

### Step 2: Run the `main.py`

Once the packages are installed, you can run the `main.py` script using Poetry:

```bash
poetry run python main.py
```

The GraphQL API will start running at `http://127.0.0.1:5081`.

### Step 3: Access GraphiQL Interface

You can access the GraphiQL interface in your browser at:

```
http://127.0.0.1:5081/graphiql
```
---

## Simple Queries

### Query 1: Get All Records from a Collection

To retrieve all records from a collection (e.g., `Course`), use the following query:

```graphql
{
  courses{
    id
    name
  }
}
```

This query will return all records from the `Course` collection, including fields such as `id` and `course`.

### Query 2: Query Across Multiple Collections

You can also query across multiple collections at the same time. For example, if you want to get the `campus` details and with a `periods` record, use the following query:

```graphql
{
  campus{
    id
    name
  }
  periods{
    id
    name
  }
}
```

This query will return data from both the `rooms` collection and the `buildings` collection, allowing you to link rooms to their respective buildings.

### Query 3: Query with relationship

To retrieve data where a nested object is part of the structure, for example, querying `rooms` that contains a reference of `campus`, use the following query:

```graphql
{
  rooms{
    id
    name
    campus{
      id
      name
    }
  }
}
```

This query will return data from the `Room` collection, including the `id`, `room`, and a nested `campus` field, which contains `id` and `campus` for each nested object.

## Parameterized Query

### Query 1: Pagination Query

Pagination queries allow you to retrieve large datasets in chunks, making it easier to handle results by limiting the number of items returned.
 To control pagination, you can pass the parameters `first`, `skip`, and `search`.
```graphql
{
  disciplines( first:2, skip:1, search:"ANÁLISE"){
    name
    course{
      id
      name
    }
  }
}
```

#### Output:
```graphql
{
  "data": {
    "disciplines": [
      {
        "name": "ANÁLISE E PROJETO DE SISTEMAS",
        "course": [
          {
            "id": 10,
            "name": "SISTEMAS DE INFORMAÇÃO (BACHARELADO)"
          },
          {
            "id": 54,
            "name": "CIÊNCIA DA COMPUTAÇÃO (BACHARELADO)"
          }
        ]
      },
      {
        "name": "ANÁLISE POLÍTICA",
        "course": [
          {
            "id": 4,
            "name": "CIÊNCIA POLÍTICA (BACHARELADO)"
          }
        ]
      }
    ]
  }
}
```

In this query:

- `first`: Defines how many results to return;
- `skip`: Skips a number of results;
- `search`: Filters results based on a search term.

This will return the second and third records that match the search term, along with their associated courses.

### Parameterized Query with Arguments:

This term emphasizes that the query accepts parameters that can alter its behavior, like `id`.

```graphql
{
  teachers(teacherId:"faca480f-4096-4027-8e4b-dfd3ef682e53"){
    id
    name
    course{
      id
      name
    }
  }
}
```

#### Output:
```graphql

{
  "data": {
    "teachers": [
      {
        "id": "faca480f-4096-4027-8e4b-dfd3ef682e53",
        "name": "WILSON AMARAL MARTINS",
        "course": [
          {
            "id": 10,
            "name": "SISTEMAS DE INFORMAÇÃO (BACHARELADO)"
          },
          {
            "id": 38,
            "name": "CST EM ANÁLISE E DESENVOLVIMENTO DE SISTEMAS"
          },
          {
            "id": 54,
            "name": "CIÊNCIA DA COMPUTAÇÃO (BACHARELADO)"
          }
        ]
      }
    ]
  }
}
```

## Read-only

The catalog only reads: the GraphQL schema has no mutations and the REST routes have no write methods. Data is loaded by the separate import procedure, not through this service.

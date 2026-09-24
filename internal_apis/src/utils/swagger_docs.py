# Swagger execution on /apidocs/


def get_swagger_specification(path, method=None):
    def pagination_parameters():
        return [
            {
                "name": "page",
                "in": "query",
                "type": "integer",
                "description": "Número da página para paginação. Valor mínimo: 1",
                "required": False,
                "default": 1,
                "minimum": 1
            },
            {
                "name": "pagesize",
                "in": "query",
                "type": "integer",
                "description": "Tamanho da página para paginação. Valor mínimo: 1, máximo: 100",
                "required": False,
                "default": 10,
                "minimum": 1,
                "maximum": 100
            }
        ]

    def pagination_response():
        return {
            "pagination": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "pagesize": {"type": "integer"},
                    "total_count": {"type": "integer"},
                    "total_pages": {"type": "integer"}
                }
            }
        }
    # Campus
    if path == 'campus' and method == 'GET':
        return {
            "summary": "Obter Campus",
            "description": "Recupera campus por ID, nome ou todos se nenhum parâmetro for fornecido.",
            "tags": ["Campus"],  # Corrigido
            "operationId": "getCampus",
            "parameters": [
                {
                    "name": "campus_id",
                    "in": "query",
                    "description": "Filtrar campus pelo ID",
                    "required": False,
                    "type": "string"
                }
            ],
            "responses": {
                "200": {
                    "description": "Campus retornado com sucesso",
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "ID do campus"
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Nome do campus"
                                }
                            }
                        }
                    }
                },
                "404": {
                    "description": "Campus não encontrado",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {
                                "type": "string",
                                "description": "Mensagem de erro"
                            }
                        }
                    }
                }
            }
        }

    # Courses
    if path == 'courses' and method == 'GET':
        return {
            "summary": "Obter Cursos",
            "description": "Recupera cursos por ID, nome ou todos se nenhum parâmetro for fornecido, com paginação.",
            "tags": ["Courses"],
            "operationId": "getCourses",
            "parameters": [
                {
                    "name": "course_id",
                    "in": "query",
                    "description": "Filtrar curso pelo ID",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "course_name",
                    "in": "query",
                    "description": "Filtrar curso pelo nome (contém)",
                    "required": False,
                    "type": "string"
                },
                # Carregar retorno dos parâmetros sobre paginação
                *pagination_parameters()
            ],
            "responses": {
                "200": {
                    "description": "Cursos retornados com sucesso",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {
                                            "type": "string",
                                            "description": "ID do curso"
                                        },
                                        "name": {
                                            "type": "string",
                                            "description": "Nome do curso"
                                        }
                                    }
                                }
                            },
                            # Carregar retorno da resposta de paginação
                            **pagination_response()
                        }
                    }
                },
                "404": {
                    "description": "Curso não encontrado",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Mensagem de erro"
                            }
                        }
                    }
                }
            }
        }

    # Disciplines
    if path == 'disciplines' and method == 'GET':
        return {
            "summary": "Obter Disciplinas",
            "description": "Recupera disciplinas por ID, nome, curso ou todas se nenhum parâmetro for fornecido, com paginação.",
            "tags": ["Disciplines"],
            "operationId": "getDisciplines",
            "parameters": [
                {
                    "name": "discipline_id",
                    "in": "query",
                    "description": "Filtrar disciplina pelo ID",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "discipline_name",
                    "in": "query",
                    "description": "Filtrar disciplina pelo nome (contém)",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "course_id",
                    "in": "query",
                    "description": "Filtrar disciplina pelo ID do curso",
                    "required": False,
                    "type": "string"
                },
                # Carregar retorno dos parâmetros sobre paginação
                *pagination_parameters()
            ],
            "responses": {
                "200": {
                    "description": "Disciplinas retornadas com sucesso",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "name": {"type": "string"},
                                        "course": {"type": "string"},
                                        "workload": {"type": "string"}
                                    }
                                }
                            },
                            # Carregar retorno da resposta de paginação
                            **pagination_response()
                        }
                    }
                },
                "404": {
                    "description": "Disciplina não encontrada",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        }
                    }
                }
            }
        }

    # Offers GET
    if path == 'offers' and method == 'GET':
        return {
            "summary": "Obter Ofertas",
            "description": "Recupera ofertas de acordo com parâmetros de filtro (offer_id, campus_id, course_id, discipline_id, period_id, room_id, teacher_id, total_enrolled), ou todas se nenhum parâmetro for fornecido, com paginação.",
            "tags": ["Offers"],
            "operationId": "getOffers",
            "parameters": [
                {
                    "name": "_id",
                    "in": "query",
                    "description": "Filtra oferta pelo ID",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "campus_id",
                    "in": "query",
                    "description": "Filtra oferta pelo ID do campus",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "course_id",
                    "in": "query",
                    "description": "Filtra oferta pelo ID do curso",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "discipline_id",
                    "in": "query",
                    "description": "Filtra oferta pelo ID da disciplina",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "period_id",
                    "in": "query",
                    "description": "Filtra oferta pelo ID do período",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "room_id",
                    "in": "query",
                    "description": "Filtra oferta pelo ID da sala",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "teacher_id",
                    "in": "query",
                    "description": "Filtra oferta pelo ID do professor",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "total_enrolled",
                    "in": "query",
                    "description": "Filtra oferta pelo número total de matriculados",
                    "required": False,
                    "type": "string"
                },
                ## add fields HERE
                {
                    "name": "total_optatives_enrolled",
                    "in": "query",
                    "description": "Filtra oferta pelo número total de matriculados em optativas",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "year",
                    "in": "query",
                    "description": "Filtra oferta pelo ano",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "semester",
                    "in": "query",
                    "description": "Filtra oferta pelo semestre",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "offer_id",
                    "in": "query",
                    "description": "Filtra oferta pelo ID da oferta",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "weekday",
                    "in": "query",
                    "description": "Filtra ofertas com aula nesse dia da semana (ISO 8601: 1 = segunda ... 7 = domingo)",
                    "required": False,
                    "type": "integer"
                },

                # Carregar retorno dos parâmetros sobre paginação
                *pagination_parameters()
            ],
            "responses": {
                "200": {
                    "description": "Ofertas retornadas com sucesso",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "discipline": {"type": "string"},
                                        "period": {"type": "string"},
                                        "campus": {"type": "string"},
                                        "room": {"type": "string"},
                                        "teacher": {"type": "string"},
                                        "total_enrolled": {"type": "integer"},
                                        "total_optatives_enrolled": {"type": "integer"},
                                        "year": {"type": "integer"},
                                        "semester": {"type": "integer"},
                                        "offer_id": {"type": "integer"},
                                        "weekdays": {"type": "array", "items": {"type": "integer"}}
                                    }
                                }
                            },
                            # Carregar retorno da resposta de paginação
                            **pagination_response()
                        }
                    }
                },
                "404": {
                    "description": "Nenhuma oferta encontrada",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    }
                }
            }
        }

    # Offers POST
    if path == 'offers' and method == 'POST':
        return {
            "summary": "Criar uma nova Oferta",
            "description": "Cria uma nova oferta de disciplina, vinculando campus, curso, disciplina, período, sala e professor.",
            "tags": ["Offers"],
            "operationId": "createOffer",
            "consumes": ["application/json"],
            "parameters": [
                {
                    "in": "header",
                    "name": "x-api-key",
                    "type": "string",
                    "required": True,
                    "description": "Chave de API para autenticação"
                },
                {
                    "in": "body",
                    "name": "offer",
                    "description": "Dados da nova oferta",
                    "required": True,
                    "schema": {
                        "type": "object",
                        "required": ["campus", "discipline", "period", "room", "teacher", "total_enrolled", "offer_id"],
                        "properties": {
                            "campus": {"type": "string", "description": "ID do campus"},
                            "discipline": {"type": "string", "description": "ID da disciplina"},
                            "period": {"type": "string", "description": "ID do período"},
                            "room": {"type": "string", "description": "ID da sala"},
                            "teacher": {"type": "string", "description": "ID do professor"},
                            "total_enrolled": {"type": "integer", "description": "Número total de matriculados"},
                            "total_optatives_enrolled": {"type": "integer", "description": "Número total de matriculados em optativas"},
                            "offer_id": {"type": "integer", "description": "ID da oferta"},
                            "weekdays": {
                                "type": "array",
                                "items": {"type": "integer", "minimum": 1, "maximum": 7},
                                "description": "Dias da semana da aula (ISO 8601: 1 = segunda ... 7 = domingo). Opcional; sem dia a oferta não bloqueia sala no Reservas."
                            }
                        }
                    }
                }
            ],
            "responses": {
                "201": {
                    "description": "Oferta criada com sucesso",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "id": {"type": "string"}
                        }
                    }
                },
                "400": {
                    "description": "Dados faltando ou inválidos",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    }
                },
                "403": {
                    "description": "Chave de API inválida ou ausente",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    }
                }
            }
        }

    # Periods
    if path == 'periods' and method == 'GET':
        return {
            "summary": "Obter Períodos",
            "description": "Recupera períodos por ID, nome ou todos se nenhum parâmetro for fornecido.",
            "tags": ["Periods"],
            "operationId": "getPeriods",
            "parameters": [
                {
                    "name": "period_id",
                    "in": "query",
                    "description": "Filtrar período pelo ID",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "period_name",
                    "in": "query",
                    "description": "Filtrar período pelo nome (contém)",
                    "required": False,
                    "type": "string"
                }
            ],
            "responses": {
                "200": {
                    "description": "Períodos retornados com sucesso",
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"}
                            }
                        }
                    }
                },
                "404": {
                    "description": "Período não encontrado",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        }
                    }
                }
            }
        }

    # Rooms
    if path == 'rooms' and method == 'GET':
        return {
            "summary": "Obter Salas",
            "description": "Recupera salas por ID, nome, campus, ou todas se nenhum parâmetro for fornecido, com paginação.",
            "tags": ["Rooms"],
            "operationId": "getRooms",
            "parameters": [
                {
                    "name": "room_id",
                    "in": "query",
                    "description": "Filtrar sala pelo ID",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "room_name",
                    "in": "query",
                    "description": "Filtrar sala pelo nome (contém)",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "campus",
                    "in": "query",
                    "description": "Filtrar sala pelo campus (contém)",
                    "required": False,
                    "type": "string"
                },
                # Carregar retorno dos parâmetros sobre paginação
                *pagination_parameters()
            ],
            "responses": {
                "200": {
                    "description": "Salas retornadas com sucesso",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "name": {"type": "string"},
                                        "campus": {"type": "string"}
                                    }
                                }
                            },
                            # Carregar retorno da resposta de paginação
                            **pagination_response()
                        }
                    }
                },
                "404": {
                    "description": "Sala não encontrada",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        }
                    }
                }
            }
        }

    # Teachers
    if path == 'teachers' and method == 'GET':
        return {
            "summary": "Obter Professores",
            "description": "Recupera professores por ID, nome, curso, ou todos se nenhum parâmetro for fornecido, com paginação.",
            "tags": ["Teachers"],
            "operationId": "getTeachers",
            "parameters": [
                {
                    "name": "teacher_id",
                    "in": "query",
                    "description": "Filtrar professor pelo ID",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "teacher_name",
                    "in": "query",
                    "description": "Filtrar professor pelo nome (contém)",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "course_id",
                    "in": "query",
                    "description": "Filtrar professor pelo ID do curso",
                    "required": False,
                    "type": "string"
                },
                # Carregar retorno dos parâmetros sobre paginação
                *pagination_parameters()
            ],
            "responses": {
                "200": {
                    "description": "Professores retornados com sucesso",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "name": {"type": "string"},
                                        "course": {"type": "string"}
                                    }
                                }
                            },
                            # Carregar retorno da resposta de paginação
                            **pagination_response()
                        }
                    }
                },
                "404": {
                    "description": "Professor não encontrado",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    }
                }
            }
        }

    # Types
    if path == 'types' and method == 'GET':
        return {
            "summary": "Obter Tipos",
            "description": "Recupera tipos por ID, nome da coleção, nome do tipo ou todos se nenhum parâmetro for fornecido.",
            "tags": ["Types"],
            "operationId": "getTypes",
            "parameters": [
                {
                    "name": "type_id",
                    "in": "query",
                    "description": "Filtrar tipo pelo ID",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "collection_name",
                    "in": "query",
                    "description": "Filtrar tipos pelo nome da coleção (contém)",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "type_name",
                    "in": "query",
                    "description": "Filtrar tipos pelo nome do tipo (contém)",
                    "required": False,
                    "type": "string"
                }
            ],
            "responses": {
                "200": {
                    "description": "Tipos retornados com sucesso",
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "types": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "type": {"type": "string"},
                                            "name": {"type": "string"}
                                        }
                                    }
                                },
                                "collection": {"type": "string"}
                            }
                        }
                    }
                },
                "404": {
                    "description": "Tipo não encontrado",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    }
                }
            }
        }
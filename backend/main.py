
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from database import engine, testar_conexao

app = FastAPI(
    title="VetCare API",
    description="API do Sistema Integrado de Gestão Hospitalar Veterinária",
    version="1.0.0"
)


# MODELO DE CADASTRO DE TUTOR
class TutorCreate(BaseModel):
    nome: str
    cpf: str
    telefone: str | None = None
    email: str | None = None
    endereco: str | None = None


class AnimalCreate(BaseModel):
    id_tutor: int
    nome: str
    especie: str
    raca: str | None = None
    sexo: str
    data_nascimento: str | None = None
    peso: float | None = None
    microchip: str | None = None
    castrado: bool = False
    observacoes: str | None = None

# ROTA INICIAL
@app.get("/")
def inicio():
    return {
        "mensagem": "Bem-vindo à API VetCare!",
        "status": "online"
    }


# VERIFICAR API
@app.get("/health")
def verificar_saude():
    return {"status": "API funcionando"}


# VERIFICAR BANCO
@app.get("/db-test")
def verificar_banco():
    return {
        "status": "Conectado",
        "banco": testar_conexao()
    }


# LISTAR TUTORES
@app.get("/tutores")
def listar_tutores():
    with engine.connect() as conexao:
        resultado = conexao.execute(text("""
            SELECT
                id_tutor,
                nome,
                cpf,
                telefone,
                email,
                endereco,
                ativo
            FROM tutores
            ORDER BY id_tutor
        """))

        tutores = [
            dict(linha)
            for linha in resultado.mappings().all()
        ]

    return tutores



# CONSULTAR TUTOR POR ID
@app.get("/tutores/{id_tutor}")
def consultar_tutor(id_tutor: int):
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT *
                FROM tutores
                WHERE id_tutor = :id_tutor
            """),
            {"id_tutor": id_tutor}
        )

        tutor = resultado.mappings().first()

    if tutor is None:
        raise HTTPException(
            status_code=404,
            detail="Tutor não encontrado."
        )

    return dict(tutor)



# ATUALIZAR TUTOR
@app.put("/tutores/{id_tutor}")
def atualizar_tutor(id_tutor: int, tutor: TutorCreate):
    with engine.begin() as conexao:
        resultado = conexao.execute(
            text("""
                UPDATE tutores
                SET
                    nome = :nome,
                    cpf = :cpf,
                    telefone = :telefone,
                    email = :email,
                    endereco = :endereco
                WHERE id_tutor = :id_tutor
                RETURNING *
            """),
            {
                **tutor.model_dump(),
                "id_tutor": id_tutor
            }
        )

        tutor_atualizado = resultado.mappings().first()

    if tutor_atualizado is None:
        raise HTTPException(
            status_code=404,
            detail="Tutor não encontrado."
        )

    return {
        "mensagem": "Tutor atualizado com sucesso!",
        "tutor": dict(tutor_atualizado)
    }

# DESATIVAR TUTOR
@app.delete("/tutores/{id_tutor}")
def desativar_tutor(id_tutor: int):
    with engine.begin() as conexao:
        resultado = conexao.execute(
            text("""
                UPDATE tutores
                SET ativo = FALSE
                WHERE id_tutor = :id_tutor
                  AND ativo = TRUE
                RETURNING id_tutor, nome, ativo
            """),
            {"id_tutor": id_tutor}
        )

        tutor = resultado.mappings().first()

    if tutor is None:
        raise HTTPException(
            status_code=404,
            detail="Tutor não encontrado ou já desativado."
        )

    return {
        "mensagem": "Tutor desativado com sucesso!",
        "tutor": dict(tutor)
    }



# CADASTRAR TUTOR
@app.post("/tutores", status_code=201)
def cadastrar_tutor(tutor: TutorCreate):
    try:
        with engine.begin() as conexao:
            resultado = conexao.execute(
                text("""
                    INSERT INTO tutores (
                        nome,
                        cpf,
                        telefone,
                        email,
                        endereco
                    )
                    VALUES (
                        :nome,
                        :cpf,
                        :telefone,
                        :email,
                        :endereco
                    )
                    RETURNING
                        id_tutor,
                        nome,
                        cpf,
                        telefone,
                        email,
                        endereco,
                        ativo
                """),
                tutor.model_dump()
            )

            novo_tutor = dict(resultado.mappings().one())

        return {
            "mensagem": "Tutor cadastrado com sucesso!",
            "tutor": novo_tutor
        }

    except Exception as erro:
        if "unique" in str(erro).lower() or "duplicate" in str(erro).lower():
            raise HTTPException(
                status_code=409,
                detail="CPF ou e-mail já cadastrado."
            )

        raise HTTPException(
            status_code=500,
            detail="Não foi possível cadastrar o tutor."
        )

    




# LISTAR ANIMAIS
@app.get("/animais")
def listar_animais():
    with engine.connect() as conexao:
        resultado = conexao.execute(text("""
            SELECT
                id_animal,
                id_tutor,
                nome,
                especie,
                raca,
                sexo,
                data_nascimento,
                peso,
                microchip,
                castrado,
                observacoes
            FROM animais
            ORDER BY id_animal
        """))

        animais = [
            dict(linha)
            for linha in resultado.mappings().all()
        ]

    return animais


# CADASTRAR ANIMAL
@app.post("/animais", status_code=201)
def cadastrar_animal(animal: AnimalCreate):
    try:
        with engine.begin() as conexao:
            resultado = conexao.execute(
                text("""
                    INSERT INTO animais (
                        id_tutor,
                        nome,
                        especie,
                        raca,
                        sexo,
                        data_nascimento,
                        peso,
                        microchip,
                        castrado,
                        observacoes
                    )
                    VALUES (
                        :id_tutor,
                        :nome,
                        :especie,
                        :raca,
                        :sexo,
                        :data_nascimento,
                        :peso,
                        :microchip,
                        :castrado,
                        :observacoes
                    )
                    RETURNING *
                """),
                animal.model_dump()
            )

            novo_animal = dict(resultado.mappings().one())

        return {
            "mensagem": "Animal cadastrado com sucesso!",
            "animal": novo_animal
        }

    except Exception as erro:
        mensagem = str(erro).lower()

        if "foreign key" in mensagem:
            raise HTTPException(
                status_code=400,
                detail="Tutor informado não existe."
            )

        if "unique" in mensagem or "duplicate" in mensagem:
            raise HTTPException(
                status_code=409,
                detail="Microchip já cadastrado."
            )

        raise HTTPException(
            status_code=500,
            detail="Não foi possível cadastrar o animal."
        )


# CONSULTAR ANIMAL POR ID
@app.get("/animais/{id_animal}")
def consultar_animal(id_animal: int):
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT *
                FROM animais
                WHERE id_animal = :id_animal
            """),
            {"id_animal": id_animal}
        )

        animal = resultado.mappings().first()

    if animal is None:
        raise HTTPException(
            status_code=404,
            detail="Animal não encontrado."
        )

    return dict(animal)



# ATUALIZAR ANIMAL
@app.put("/animais/{id_animal}")
def atualizar_animal(id_animal: int, animal: AnimalCreate):
    with engine.begin() as conexao:
        resultado = conexao.execute(
            text("""
                UPDATE animais
                SET
                    id_tutor = :id_tutor,
                    nome = :nome,
                    especie = :especie,
                    raca = :raca,
                    sexo = :sexo,
                    data_nascimento = :data_nascimento,
                    peso = :peso,
                    microchip = :microchip,
                    castrado = :castrado,
                    observacoes = :observacoes
                WHERE id_animal = :id_animal
                RETURNING *
            """),
            {
                **animal.model_dump(),
                "id_animal": id_animal
            }
        )

        animal_atualizado = resultado.mappings().first()

    if animal_atualizado is None:
        raise HTTPException(
            status_code=404,
            detail="Animal não encontrado."
        )

    return {
        "mensagem": "Animal atualizado com sucesso!",
        "animal": dict(animal_atualizado)
    }

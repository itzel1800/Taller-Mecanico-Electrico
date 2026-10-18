import mssql_python
import json
from dotenv import load_dotenv
import os


class ConexionSqlServer:
    def __init__(self):
        load_dotenv(override=True)
        self.SERVER = os.getenv('SERVER_NAME')
        self.DATABASE_NAME = os.getenv('DATABASE_NAME')
        self.USER = os.getenv('USER')
        self.PASSWORD = os.getenv('PASSWORD')

        self.CNX = None     # Gestionar la conexion
        self.CURSOR = None  # Gestionar las consultas

    def consulta(self, sql, parametros=None):
        try:
            # Si no hay conexión, intento conectarme
            if self.CURSOR is None:
                if self.crear_conexion() is None:
                    return json.dumps(
                        {
                            'estado': False,
                            'mensaje': 'No fue posible establecer la conexion'
                        },
                        ensure_ascii=False
                    )

            # Ejecutar la consulta (con o sin parmetros)
            if parametros:
                self.CURSOR.execute(sql, parametros)
            else:
                self.CURSOR.execute(sql)

            # Identificar la operacion: SELECT, INSERT, UPDATE, DELETE
            tipo = sql.split()[0].strip().upper()

            # SELECT
            if tipo == 'SELECT':
                columnas = []
                for columna in self.CURSOR.description:
                    columnas.append(columna[0])
                registros = self.CURSOR.fetchall()
                resultados = []
                for registro in registros:
                    fila = {}
                    for i, valor in enumerate(registro):
                        fila[columnas[i]] = valor
                    resultados.append(fila)
                return json.dumps(
                    {
                        'estado': True,
                        'tipo': 'select',
                        'registros': resultados
                    },
                    ensure_ascii=False,
                    default=str
                )

            # INSERT
            elif tipo == "INSERT":
                filas = self.CURSOR.rowcount  # Num de registros afectados
                self.CNX.commit()             # Guarda la transaccin
                return json.dumps(
                    {
                        "estado": True,
                        "tipo": "INSERT",
                        "mensaje": "Registro insertado correctamente",
                        "filas_afectadas": filas
                    },
                    ensure_ascii=False
                )

            # UPDATE
            elif tipo == "UPDATE":
                filas = self.CURSOR.rowcount
                self.CNX.commit()
                return json.dumps(
                    {
                        "estado": True,
                        "tipo": "UPDATE",
                        "mensaje": "Registro actualizado correctamente",
                        "filas_afectadas": filas
                    },
                    ensure_ascii=False
                )

            # DELETE
            elif tipo == "DELETE":
                filas = self.CURSOR.rowcount
                self.CNX.commit()
                return json.dumps(
                    {
                        "estado": True,
                        "tipo": "DELETE",
                        "mensaje": "Registro eliminado correctamente",
                        "filas_afectadas": filas
                    },
                    ensure_ascii=False
                )

            else:
                filas = self.CURSOR.rowcount
                self.CNX.commit()
                return json.dumps(
                    {
                        "estado": True,
                        "tipo": tipo,
                        "mensaje": "Consulta ejecutada correctamente",
                        "filas_afectadas": filas
                    },
                    ensure_ascii=False
                )

        # ERROR DE INTEGRIDAD (llaves foráneas, duplicados, etc.)
        except mssql_python.IntegrityError as e:
            if self.CNX:
                self.CNX.rollback()
            return json.dumps(
                {
                    "estado": False,
                    "tipo": "IntegrityError",
                    "mensaje": "Violación de integridad en la base de datos",
                    "error": str(e)
                },
                ensure_ascii=False
            )
        # ERROR DE PROGRAMACION S (consulta mal escrita)
        except mssql_python.ProgrammingError as e:
            if self.CNX:
                self.CNX.rollback()
            return json.dumps(
                {
                    "estado": False,
                    "tipo": "ProgrammingError",
                    "mensaje": "Error en la consulta SQL",
                    "error": str(e)
                },
                ensure_ascii=False
            )
        # ERROR GENERAL DE BASE DE DATOS
        except mssql_python.Error as e:
            if self.CNX:
                self.CNX.rollback()
            return json.dumps(
                {
                    "estado": False,
                    "tipo": "DatabaseError",
                    "mensaje": "Error en la base de datos",
                    "error": str(e)
                },
                ensure_ascii=False
            )
        # ERROR DE PYTHON
        except Exception as e:
            if self.CNX:
                self.CNX.rollback()
            return json.dumps(
                {
                    "estado": False,
                    "tipo": "Error",
                    "mensaje": "Error inesperado",
                    "error": str(e)
                },
                ensure_ascii=False
            )

    def crear_conexion(self):
        try:
            servidor = str(self.SERVER)
            cadena_con = (
                f"Server={servidor};"
                f"Database={self.DATABASE_NAME};"
                f"UID={self.USER};"
                f"PWD={self.PASSWORD};"
                "Encrypt=yes;"
                "TrustServerCertificate=yes;"
            )
            self.CNX = mssql_python.connect(cadena_con)
            self.CURSOR = self.CNX.cursor()
            print(f"Conectado al servidor {self.SERVER}")
        except mssql_python.Error as e:
            print(f"Error al conectarse al servidor {self.SERVER} de base de datos")
            print(e)
            self.CNX = None
            self.CURSOR = None
        return self.CNX

    def cerrar_conexion(self):
        ban = False
        try:
            if self.CURSOR:
                self.CURSOR.close()
                self.CURSOR = None
            if self.CNX:
                self.CNX.close()   # cierra   la conexion
                self.CNX = None
            ban = True
            print("se ha cerrado la conexion")
        except mssql_python.Error as e:
            print("Error al desconectarse de la base de datos")
            print(e)
        return ban

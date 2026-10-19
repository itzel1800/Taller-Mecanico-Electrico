import json
import tkinter as tk
from tkinter import ttk, messagebox

from conexion_sqlserver import ConexionSqlServer
from conexion_postgresql import ConexionPostgreSql

# ==========================================
# PALETA DE COLORES DE LA INTERFAZ
# ==========================================
AZUL_OSCURO = "#123B5D"
AZUL = "#176B87"
VERDE = "#BCEAD5"
VERDE_CLARO = "#F0FAF5"
BLANCO = "#FFFFFF"
TEXTO = "#183746"
GRIS = "#6B7C85"

# ==========================================
# CATÁLOGOS (DEFINICIÓN DE TABLAS Y CAMPOS)
# ==========================================
CATALOGOS = {
    "Clientes": {
        "pk": "Id_Cliente",
        "campos": [("Nombre", "Nombre", True), ("Apellido", "Apellido", True),
                   ("Telefono", "Teléfono", True), ("Correo", "Correo", False)],
    },
    "Vehiculos": {
        "pk": "Id_Vehiculo",
        "campos": [("Id_Cliente", "ID del cliente", True), ("Marca", "Marca", True),
                   ("Modelo", "Modelo", True), ("Anio", "Año", False),
                   ("Placa", "Placa", True), ("Color", "Color", False),
                   ("Kilometraje", "Kilometraje", False)],
    },
    "Mecanicos": {
        "pk": "Id_Mecanico",
        "campos": [("Nombre", "Nombre", True), ("Apellido", "Apellido", True),
                   ("Especialidad", "Especialidad", True), ("Telefono", "Teléfono", True),
                   ("Estado", "Estado (ACTIVO/INACTIVO)", True)],
    },
    "Servicios": {
        "pk": "Id_Servicio",
        "campos": [("Nombre", "Nombre", True), ("Descripcion", "Descripción", True),
                   ("Precio", "Precio", True)],
    },
    "Categorias": {
        "pk": "Id_Categoria",
        "campos": [("Nombre", "Nombre", True), ("Descripcion", "Descripción", False)],
    },
    "Refacciones": {
        "pk": "Id_Refaccion",
        "campos": [("Id_Categoria", "ID de categoría", True), ("Nombre", "Nombre", True),
                   ("Marca", "Marca", True), ("Numero_Parte", "Número de parte", True),
                   ("Costo", "Costo", True), ("Precio_Venta", "Precio de venta", True),
                   ("Existencia", "Existencia", True)],
    },
    "Proveedores": {
        "pk": "Id_Proveedor",
        "campos": [("Nombre", "Nombre", True), ("Telefono", "Teléfono", True),
                   ("Correo", "Correo", False), ("Ciudad", "Ciudad", True)],
    },
}


class MenuTallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Taller Ochoa | Sistema de administración")
        self.root.geometry("1180x740")
        self.root.minsize(980, 620)
        self.root.configure(bg=VERDE_CLARO)

        # Variables de control de la Base de Datos
        self.conn = None
        self.motor = None
        self.nombre_motor = ""
        self.ph = "?"  # Marcador de parámetros: SQL Server usa '?' y PostgreSQL usa '%s'
        self.conectado = False
        
        # Variables de control de la interfaz y catálogos
        self.catalogo_actual = None
        self.campos_formulario = {}
        self.id_seleccionado = None
        self.nav_buttons = {}

        self._configurar_estilos()
        self._construir_estructura()
        self.mostrar_inicio()

    def _configurar_estilos(self):
        """Configura los estilos visuales de la tabla (Treeview) y componentes."""
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("Treeview", background=BLANCO, foreground=TEXTO,
                         fieldbackground=BLANCO, rowheight=28, font=("Segoe UI", 9))
        estilo.configure("Treeview.Heading", background=AZUL, foreground=BLANCO,
                         font=("Segoe UI", 9, "bold"), padding=7)
        estilo.map("Treeview", background=[("selected", VERDE)])
        estilo.configure("TCombobox", padding=5)

    def _construir_estructura(self):
        """Construye el diseño estático principal: Encabezado, Menú lateral y Pie de página."""
        # 1. Encabezado superior
        encabezado = tk.Frame(self.root, bg=AZUL_OSCURO, height=82)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        
        tk.Label(encabezado, text="OCHOA", bg=AZUL_OSCURO, fg=BLANCO,
                 font=("Segoe UI", 22, "bold")).pack(side="left", padx=(25, 15), pady=15)
        tk.Label(encabezado, text="TALLER MECÁNICO ELÉCTRICO\nSistema de administración",
                 bg=AZUL_OSCURO, fg="#D7F4EA", justify="left",
                 font=("Segoe UI", 10)).pack(side="left", pady=15)
                 
        self.lbl_estado = tk.Label(encabezado, text="● Sin conexión", bg=AZUL_OSCURO,
                                   fg="#FFE4A8", font=("Segoe UI", 10, "bold"))
        self.lbl_estado.pack(side="right", padx=25)

        # 2. Cuerpo y Barra Lateral de Navegación
        cuerpo = tk.Frame(self.root, bg=VERDE_CLARO)
        cuerpo.pack(fill="both", expand=True)
        
        barra = tk.Frame(cuerpo, bg=AZUL, width=225)
        barra.pack(side="left", fill="y")
        barra.pack_propagate(False)
        
        tk.Label(barra, text="MENÚ PRINCIPAL", bg=AZUL, fg="#D7F4EA",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=18, pady=(22, 12))

        opciones = [("inicio", "⌂   Inicio"), ("catalogos", "▦   Catálogos"),
                    ("conexion", "⇄   Base de datos")]
        for clave, texto in opciones:
            boton = tk.Button(barra, text=texto, anchor="w", relief="flat", bd=0,
                              cursor="hand2", padx=17, pady=13, bg=AZUL, fg=BLANCO,
                              activebackground=VERDE, activeforeground=AZUL_OSCURO,
                              font=("Segoe UI", 10, "bold"),
                              command=lambda c=clave: self.navegar(c))
            boton.pack(fill="x", padx=8, pady=3)
            self.nav_buttons[clave] = boton

        tk.Label(barra, text="TABLAS MAESTRAS", bg=AZUL, fg="#D7F4EA",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(20, 8))
        for tabla in CATALOGOS:
            boton = tk.Button(barra, text="•   " + tabla, anchor="w", relief="flat", bd=0,
                              cursor="hand2", padx=19, pady=7, bg=AZUL, fg=BLANCO,
                              activebackground=VERDE, activeforeground=AZUL_OSCURO,
                              font=("Segoe UI", 9),
                              command=lambda t=tabla: self.abrir_catalogo(t))
            boton.pack(fill="x", padx=8, pady=1)

        # Panel dinámico central
        self.panel = tk.Frame(cuerpo, bg=VERDE_CLARO)
        self.panel.pack(side="left", fill="both", expand=True, padx=24, pady=22)

        # 3. Pie de página
        pie = tk.Frame(self.root, bg=BLANCO, height=30)
        pie.pack(fill="x", side="bottom")
        pie.pack_propagate(False)
        tk.Label(pie, text="Sistema de administración • Taller Ochoa", bg=BLANCO,
                 fg=GRIS, font=("Segoe UI", 9)).pack(side="left", padx=18, pady=6)
        tk.Label(pie, text="Python + Tkinter", bg=BLANCO, fg=GRIS,
                 font=("Segoe UI", 9)).pack(side="right", padx=18, pady=6)

    def limpiar_panel(self):
        """Elimina todos los elementos actuales del panel central para redibujar otra vista."""
        for widget in self.panel.winfo_children():
            widget.destroy()

    def titulo_panel(self, titulo, subtitulo=""):
        """Coloca un título y subtítulo estándar en la parte superior del panel central."""
        tk.Label(self.panel, text=titulo, bg=VERDE_CLARO, fg=AZUL_OSCURO,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w")
        if subtitulo:
            tk.Label(self.panel, text=subtitulo, bg=VERDE_CLARO, fg=GRIS,
                     font=("Segoe UI", 10), wraplength=850, justify="left").pack(anchor="w", pady=(4, 16))

    def navegar(self, opcion):
        """Controla el cambio de pestañas principales (Inicio, Catálogos, Base de datos)."""
        for clave, boton in self.nav_buttons.items():
            boton.configure(bg=VERDE if clave == opcion else AZUL,
                            fg=AZUL_OSCURO if clave == opcion else BLANCO)
        if opcion == "inicio":
            self.mostrar_inicio()
        elif opcion == "conexion":
            self.mostrar_conexion()
        elif opcion == "catalogos":
            self.mostrar_catalogos()

    # ==========================================
    # VISTAS PRINCIPALES (PANTALLAS)
    # ==========================================
    def mostrar_inicio(self):
        """Dibuja la pantalla de bienvenida con tarjetas de acceso rápido a catálogos."""
        self.limpiar_panel()
        self.titulo_panel("¡Bienvenido!", "Administra los catálogos del taller desde este menú principal.")
        
        estado = (f"Conectado a {self.nombre_motor}" if self.conectado
                  else "Selecciona Base de datos para conectarte antes de usar los catálogos.")
        color = "#DDF5E7" if self.conectado else "#FFF0CF"
        
        tk.Label(self.panel, text="●  " + estado, bg=color, fg=AZUL_OSCURO,
                 font=("Segoe UI", 10, "bold"), padx=15, pady=14,
                 wraplength=800, justify="left").pack(fill="x", pady=(0, 18))
                 
        tk.Label(self.panel, text="Catálogos disponibles", bg=VERDE_CLARO, fg=AZUL_OSCURO,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))
                 
        tarjetas = tk.Frame(self.panel, bg=VERDE_CLARO)
        tarjetas.pack(fill="both", expand=True)
        for columna in range(3):
            tarjetas.columnconfigure(columna, weight=1)
            
        for indice, tabla in enumerate(CATALOGOS):
            tarjeta = tk.Frame(tarjetas, bg=BLANCO, highlightbackground="#D7E9E2", highlightthickness=1)
            tarjeta.grid(row=indice // 3, column=indice % 3, sticky="nsew", padx=6, pady=6)
            
            tk.Label(tarjeta, text=tabla, bg=BLANCO, fg=AZUL_OSCURO,
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(14, 5))
            tk.Label(tarjeta, text="Insertar · Actualizar · Eliminar · Consultar",
                     bg=BLANCO, fg=GRIS, font=("Segoe UI", 8), wraplength=210,
                     justify="left").pack(anchor="w", padx=14, pady=(0, 10))
            tk.Button(tarjeta, text="Abrir catálogo →", bg=AZUL, fg=BLANCO, relief="flat",
                      cursor="hand2", padx=10, pady=7,
                      command=lambda t=tabla: self.abrir_catalogo(t)).pack(anchor="w", padx=14, pady=(0, 14))
                      
        for fila in range(3):
            tarjetas.rowconfigure(fila, weight=1)

    def mostrar_catalogos(self):
        """Muestra la lista de botones para elegir qué tabla administrar."""
        self.limpiar_panel()
        self.titulo_panel("Catálogos", "Selecciona una tabla maestra para administrar sus registros.")
        for tabla in CATALOGOS:
            tk.Button(self.panel, text=tabla + "   →", anchor="w", bg=BLANCO, fg=AZUL_OSCURO,
                      activebackground=VERDE, relief="flat", cursor="hand2", padx=16, pady=11,
                      font=("Segoe UI", 11, "bold"),
                      command=lambda t=tabla: self.abrir_catalogo(t)).pack(fill="x", pady=4)

    def mostrar_conexion(self):
        """Muestra la interfaz para elegir y activar la conexión a la base de datos."""
        self.limpiar_panel()
        self.titulo_panel("Base de datos", "Elige el motor configurado en tu archivo .env.")
        
        caja = tk.Frame(self.panel, bg=BLANCO, highlightbackground="#D7E9E2", highlightthickness=1)
        caja.pack(fill="x", pady=6)
        
        tk.Label(caja, text="Motor de base de datos", bg=BLANCO, fg=AZUL_OSCURO,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20, pady=(20, 8))
                 
        self.motor_var = tk.StringVar(value=self.nombre_motor or "SQL Server")
        ttk.Combobox(caja, textvariable=self.motor_var, values=["SQL Server", "PostgreSQL"],
                     state="readonly", width=28).pack(anchor="w", padx=20, pady=5)
                     
        tk.Label(caja, text="Verifica que el servidor esté activo y que las credenciales del .env sean correctas.",
                 bg=BLANCO, fg=GRIS, wraplength=700, justify="left").pack(anchor="w", padx=20, pady=12)
                 
        tk.Button(caja, text="Conectar", command=self.conectar, bg=AZUL, fg=BLANCO,
                  relief="flat", cursor="hand2", padx=18, pady=9).pack(anchor="w", padx=20, pady=(0, 20))
                  
        if self.conectado:
            tk.Label(self.panel, text=f"Conexión activa: {self.nombre_motor}", bg=VERDE_CLARO,
                     fg="#23734D", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=10)

    # ==========================================
    # GESTIÓN DE CONEXIONES (AQUÍ SE CREAN Y CIERRAN)
    # ==========================================
    def conectar(self):
        """Aquí se CREA la conexión con el servidor seleccionado (SQL Server o PostgreSQL)."""
        self.cerrar_conexion(mostrar_estado=False)
        motor_elegido = self.motor_var.get()
        
        try:
            # 1. Instanciamos la clase correspondiente según el motor elegido
            if motor_elegido == "SQL Server":
                conexion = ConexionSqlServer()
                placeholder = "?"
                motor = "sqlserver"
            else:
                conexion = ConexionPostgreSql()
                placeholder = "%s"
                motor = "postgresql"
                
            # 2. Ejecutamos el método para abrir la conexión
            resultado = conexion.crear_conexion()
            if resultado is None:
                messagebox.showerror("Conexión fallida", "No fue posible conectar. Revisa el servidor y el archivo .env.")
                return
                
            # 3. Guardamos los objetos de conexión en variables globales de la app
            self.conn = conexion
            self.ph = placeholder
            self.motor = motor
            self.nombre_motor = motor_elegido
            self.conectado = True
            
            self.lbl_estado.configure(text=f"● Conectado: {self.nombre_motor}", fg=VERDE)
            messagebox.showinfo("Conexión correcta", f"Conexión con {self.nombre_motor} establecida.")
            self.mostrar_inicio()
            
        except Exception as error:
            self.conn = None
            self.conectado = False
            self.lbl_estado.configure(text="● Sin conexión", fg="#FFE4A8")
            messagebox.showerror("Error de conexión", str(error))

    def cerrar_conexion(self, mostrar_estado=True):
        """Aquí se CIERRA la conexión activa con la base de datos."""
        if self.conn:
            try:
                self.conn.cerrar_conexion()  # Método provisto por tus clases de conexión
            except Exception:
                pass
        self.conn = None
        self.conectado = False
        if mostrar_estado and hasattr(self, "lbl_estado"):
            self.lbl_estado.configure(text="● Sin conexión", fg="#FFE4A8")

    def ejecutar(self, sql, parametros=None):
        """Punto central para enviar consultas SQL parametrizadas a la base de datos."""
        if not self.conectado or not self.conn:
            raise RuntimeError("Primero conecta una base de datos desde Base de datos.")
            
        respuesta = json.loads(self.conn.consulta(sql, parametros))
        if not respuesta.get("estado"):
            raise RuntimeError(respuesta.get("mensaje") or respuesta.get("error") or "La consulta no se pudo completar.")
            
        if respuesta.get("registros"):
            respuesta["registros"] = [
                {str(clave).lower(): valor for clave, valor in registro.items()}
                for registro in respuesta["registros"]
            ]
        return respuesta

    # ==========================================
    # INTERFAZ Y OPERACIONES DE CATÁLOGOS (CRUD)
    # ==========================================
    def abrir_catalogo(self, tabla):
        """Abre la vista de gestión para una tabla específica (Muestra formulario y tabla visual)."""
        if not self.conectado:
            messagebox.showwarning("Sin conexión", "Conecta primero la base de datos.")
            self.navegar("conexion")
            return
            
        self.catalogo_actual = tabla
        self.id_seleccionado = None
        self.limpiar_panel()
        self.titulo_panel(tabla, "Selecciona un registro y utiliza Insertar, Actualizar, Eliminar o Consultar.")
        
        # Botones de acción (CRUD)
        acciones = tk.Frame(self.panel, bg=VERDE_CLARO)
        acciones.pack(fill="x", pady=(0, 10))
        
        botones = [
            ("Insertar", self.limpiar_formulario), 
            ("Actualizar", self.preparar_actualizacion),
            ("Eliminar", self.eliminar_seleccionado), 
            ("Consultar / Actualizar lista", self.consultar_catalogo)
        ]
        
        for texto, comando in botones:
            tk.Button(acciones, text=texto, command=comando, bg=AZUL if texto != "Eliminar" else "#B94A48",
                      fg=BLANCO, relief="flat", cursor="hand2", padx=12, pady=8,
                      font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 7))

        # Formulario dinámico para capturar datos
        marco_form = tk.LabelFrame(self.panel, text="Datos del registro", bg=BLANCO, fg=AZUL_OSCURO,
                                   font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        marco_form.pack(fill="x", pady=(0, 10))
        
        self.campos_formulario = {}
        config = CATALOGOS[tabla]
        
        # Campo de Llave Primaria (Solo lectura)
        self.id_var = tk.StringVar()
        tk.Label(marco_form, text=config["pk"], bg=BLANCO, fg=TEXTO).grid(row=0, column=0, sticky="w", padx=6, pady=5)
        self.id_entry = tk.Entry(marco_form, textvariable=self.id_var, state="readonly", width=18)
        self.id_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=5)

        # Generar campos de entrada dinámicamente distribuidos en 2 columnas
        max_fila = 0
        for indice, (campo, etiqueta, obligatorio) in enumerate(config["campos"], start=1):
            fila = (indice // 2) + 1
            columna = (indice % 2) * 2
            max_fila = max(max_fila, fila)
            
            tk.Label(marco_form, text=etiqueta + (" *" if obligatorio else ""), bg=BLANCO,
                     fg=TEXTO).grid(row=fila, column=columna, sticky="w", padx=6, pady=5)
                     
            entrada = tk.Entry(marco_form, width=27, relief="solid", bd=1, bg="#FAFDFC")
            entrada.grid(row=fila, column=columna + 1, sticky="ew", padx=6, pady=5, ipady=4)
            self.campos_formulario[campo] = (entrada, obligatorio)

        for col in range(4):
            marco_form.columnconfigure(col, weight=1 if col % 2 else 0)

        # Botón para Guardar (Sirve tanto para NUEVO como para EDITAR) - Ubicado de forma segura en la siguiente fila
        ultima_fila = max_fila + 1
        tk.Button(marco_form, text="Guardar registro", command=self.guardar_registro, bg=VERDE,
                  fg=AZUL_OSCURO, relief="flat", cursor="hand2", padx=14, pady=8,
                  font=("Segoe UI", 9, "bold")).grid(row=ultima_fila, column=0, columnspan=4, sticky="w", padx=6, pady=(12, 8))

        # Tabla visual (Treeview) para mostrar registros
        marco_tabla = tk.Frame(self.panel, bg=VERDE_CLARO)
        marco_tabla.pack(fill="both", expand=True)
        
        self.tabla_tree = ttk.Treeview(marco_tabla, show="headings", selectmode="browse")
        scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.tabla_tree.yview)
        scroll_x = ttk.Scrollbar(marco_tabla, orient="horizontal", command=self.tabla_tree.xview)
        
        self.tabla_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tabla_tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        marco_tabla.rowconfigure(0, weight=1)
        marco_tabla.columnconfigure(0, weight=1)
        
        # Evento cuando el usuario selecciona un renglón de la tabla
        self.tabla_tree.bind("<<TreeviewSelect>>", self.seleccionar_registro)
        self.consultar_catalogo()

    def consultar_catalogo(self):
        """CONSULTA (Read): Carga todos los registros de la tabla activa en la interfaz."""
        if not self.catalogo_actual or not self.conectado:
            return
            
        tabla = self.catalogo_actual
        config = CATALOGOS[tabla]
        columnas = [config["pk"]] + [campo[0] for campo in config["campos"]]
        sql = f"SELECT {', '.join(columnas)} FROM {tabla} ORDER BY {config['pk']};"
        
        try:
            registros = self.ejecutar(sql).get("registros", [])
            self.tabla_tree.delete(*self.tabla_tree.get_children())
            self.tabla_tree["columns"] = columnas
            
            for columna in columnas:
                self.tabla_tree.heading(columna, text=columna.replace("_", " "))
                self.tabla_tree.column(columna, width=125, minwidth=80, stretch=True, anchor="w")
                
            for registro in registros:
                valores = [registro.get(columna.lower()) for columna in columnas]
                self.tabla_tree.insert("", "end", values=["" if v is None else v for v in valores])
                
        except Exception as error:
            messagebox.showerror("Error al consultar", str(error))

    def seleccionar_registro(self, _evento=None):
        """BUSCA Y CARGA los datos del registro que el usuario selecciona en la tabla hacia el formulario."""
        seleccion = self.tabla_tree.selection()
        if not seleccion:
            return
            
        valores = self.tabla_tree.item(seleccion[0], "values")
        columnas = list(self.tabla_tree["columns"])
        if not valores:
            return
            
        # Obtenemos el ID de la primera columna (Llave Primaria)
        self.id_seleccionado = valores[0]
        self.id_var.set(str(valores[0]))
        
        # Rellenamos cada caja de texto con su valor correspondiente
        for campo, (entrada, _obligatorio) in self.campos_formulario.items():
            entrada.delete(0, "end")
            if campo in columnas:
                valor = valores[columnas.index(campo)]
                entrada.insert(0, "" if valor is None else str(valor))

    def limpiar_formulario(self):
        """Limpia el formulario para permitir ingresar un registro completamente nuevo."""
        self.id_seleccionado = None
        self.id_var.set("")
        for entrada, _obligatorio in self.campos_formulario.values():
            entrada.delete(0, "end")
        if hasattr(self, "tabla_tree"):
            for seleccionado in self.tabla_tree.selection():
                self.tabla_tree.selection_remove(seleccionado)

    def preparar_actualizacion(self):
        """Avisa al usuario que seleccione un elemento para actualizar."""
        if not self.id_seleccionado:
            messagebox.showwarning("Selecciona un registro", "Selecciona una fila de la tabla que deseas actualizar.")
            return
        messagebox.showinfo("Actualizar", "Modifica los campos del formulario y pulsa Guardar registro.")

    def guardar_registro(self):
        """CREAR (Insert) o ACTUALIZAR (Update): Decide qué acción realizar dependiendo si hay un ID seleccionado."""
        tabla = self.catalogo_actual
        if not tabla:
            return
            
        config = CATALOGOS[tabla]
        valores = {}
        
        # Validación de campos obligatorios
        for campo, (entrada, obligatorio) in self.campos_formulario.items():
            valor = entrada.get().strip()
            if obligatorio and not valor:
                messagebox.showwarning("Campo obligatorio", f"Completa el campo: {campo}.")
                entrada.focus_set()
                return
            valores[campo] = valor if valor != "" else None
            
        try:
            # SI HAY UN ID SELECCIONADO -> ACTUALIZAR (UPDATE)
            if self.id_var.get().strip():
                asignaciones = ", ".join(f"{campo} = {self.ph}" for campo in valores)
                sql = f"UPDATE {tabla} SET {asignaciones} WHERE {config['pk']} = {self.ph};"
                parametros = tuple(valores.values()) + (self.convertir_id(self.id_var.get()),)
                
                self.ejecutar(sql, parametros)
                mensaje = "Registro actualizado correctamente."
                
            # SI NO HAY ID -> INSERTAR NUEVO (INSERT)
            else:
                campos = list(valores.keys())
                marcadores = ", ".join([self.ph] * len(campos))
                sql = f"INSERT INTO {tabla} ({', '.join(campos)}) VALUES ({marcadores});"
                parametros = tuple(valores.values())
                
                self.ejecutar(sql, parametros)
                mensaje = "Registro insertado correctamente."
                
            messagebox.showinfo("Operación correcta", mensaje)
            self.limpiar_formulario()
            self.consultar_catalogo()
            
        except Exception as error:
            messagebox.showerror("No se pudo guardar", f"{error}\n\nVerifica los datos, las llaves relacionadas y los valores permitidos.")

    @staticmethod
    def convertir_id(valor):
        """Convierte el ID de texto a entero si es numérico."""
        try:
            return int(valor)
        except (TypeError, ValueError):
            return valor

    def eliminar_seleccionado(self):
        """ELIMINAR (Delete): Borra el registro seleccionado actualmente usando su Llave Primaria."""
        if not self.id_seleccionado:
            messagebox.showwarning("Selecciona un registro", "Selecciona una fila de la tabla que deseas eliminar.")
            return
            
        tabla = self.catalogo_actual
        config = CATALOGOS[tabla]
        
        confirmar = messagebox.askyesno("Confirmar eliminación",
                                        f"¿Deseas eliminar el registro {self.id_seleccionado} de {tabla}?\nEsta acción no se puede deshacer.")
        if not confirmar:
            return
            
        try:
            sql = f"DELETE FROM {tabla} WHERE {config['pk']} = {self.ph};"
            self.ejecutar(sql, (self.convertir_id(self.id_seleccionado),))
            
            messagebox.showinfo("Operación correcta", "Registro eliminado correctamente.")
            self.limpiar_formulario()
            self.consultar_catalogo()
            
        except Exception as error:
            messagebox.showerror("No se pudo eliminar", f"{error}\n\nSi el registro tiene información relacionada, primero revisa sus dependencias.")

    def salir(self):
        """Cierra la conexión activa y destruye la ventana principal."""
        self.cerrar_conexion()
        self.root.destroy()


if __name__ == "__main__":
    ventana = tk.Tk()
    app = MenuTallerApp(ventana)
    ventana.protocol("WM_DELETE_WINDOW", app.salir)
    ventana.mainloop()
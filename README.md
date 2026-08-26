# Sistema de Análisis de Ventas y ETL - TechData

## Contexto de la Empresa

**TechData** opera comercialmente en 5 ciudades clave de Colombia: **Santa Marta, Barranquilla, Cartagena, Montería y Bogotá**.

Debido a que el equipo de contabilidad consolidaba todas las operaciones en una única planilla de cálculo descentralizada, la organización enfrentaba graves problemas de calidad de datos:

* Inconsistencias de formato y tildes en nombres de vendedores, ciudades y categorías.
* Valores monetarios mezclados con cadenas de texto y símbolos de moneda (`$`, `.`, `,`).
* Presencia de registros nulos, datos faltantes y filas duplicadas.

Este proyecto implementa una solución de ingeniería de datos completa: un **pipeline ETL** en Python para la limpieza y estructuración en un **modelo dimensional (Estrella)** alojado en PostgreSQL (Neon), junto con un dashboard analítico en Power BI para el seguimiento de KPIs y OKRs.

---

## Tecnologías Utilizadas y Justificación

| Tecnología                 | Versión        | Propósito / Rol en el Proyecto                                                   | Justificación Técnica                                                                                                                        |
| :-------------------------- | :-------------- | :-------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------- |
| **Python**            | `>=2.2 / 3.x` | Lenguaje de programación principal para el script ETL.                           | Estándar de la industria en ciencia de datos e ingeniería de datos gracias a su ecosistema de librerías maduras y legibilidad.              |
| **Pandas**            | `>=2.2`       | Limpieza, transformación y normalización del dataset CSV.                       | Permite manipulación vectorial de datos tabulares de alta velocidad y manejo eficiente de valores faltantes (`NA`).                         |
| **SQLAlchemy**        | `>=2.0`       | ORM y capa de abstracción de bases de datos relacionales.                        | Permite gestionar conexiones seguras y transacciones robustas hacia PostgreSQL de forma agnóstica al motor.                                   |
| **Psycopg2-binary**   | `>=2.9`       | Conector binario de PostgreSQL para Python.                                       | Driver optimizado en C para la comunicación de alto rendimiento con bases de datos PostgreSQL.                                                |
| **Python-Dotenv**     | `>=1.0`       | Gestión de variables de entorno seguras.                                         | Evita hardcodear credenciales sensibles de conexión a bases de datos en el código fuente.                                                    |
| **PostgreSQL (Neon)** | Cloud           | Almacenamiento relacional en la nube bajo un esquema en Estrella.                 | Base de datos relacional empresarial con soporte robusto para integridad referencial (`PRIMARY KEY`, `FOREIGN KEY`) y alta disponibilidad. |
| **Power BI Desktop**  | Última         | Visualización de datos, modelado semántico y Business Intelligence (`.pbix`). | Herramienta líder para la creación de dashboards interactivos y toma de decisiones gerenciales.                                              |

---

## Arquitectura y Estructura del Proyecto

El proyecto sigue una arquitectura modular orientada a datos:

```text
TechData/
│
├── dataset_sucio_tienda_tecnologia.csv      # Datos crudos originales con inconsistencias
├── dataset_limpio_tienda_tecnologia.csv     # Dataset procesado y normalizado
├── tecnologia.py                            # Script ETL principal (Limpieza + Modelo Dimensional + Carga DB)
├── Tecno.pbix                               # Dashboard analítico en Power BI
├── requirements.txt                         # Dependencias del proyecto
├── .env                                     # Credenciales de conexión (Omitido en Git)
├── .gitignore                               # Archivos excluidos del control de versiones
└── README.md                                # Documentación técnica del proyecto
```

---

### Modelo Dimensional (Esquema en Estrella)

- ****Tabla de Hechos:**** `ft_ventas` (Mide el valor de las transacciones, cantidades, descuentos y métodos de pago).
- ****Dimensiones:****
- - `dim_cliente` (Nombre, correo, tipo de cliente).
  - `dim_producto` (Nombre del producto, categoría, precio unitario).
  - `dim_vendedor` (Nombre del asesor comercial).
  - `dim_ubicacion` (`ciudad`, `region`).

## Preguntas de Negocio que Responde el Dashboard (`.pbix`)

El modelo analítico implementado en Power BI permite responder a las siguientes preguntas estratégicas para la gerencia de TechData:

1. - ¿Cuál es la ciudad y región con mayor volumen de ventas asociadas de cierta categoria?
2. - ¿Como se movieron las ventas en el transcurso de el año registrado?
3. - ¿Cuáles son las categorías de productos (Computadores, Periféricos, Monitores, etc.) que lideran la rotación y el ingreso total?
4. - ¿Cuál es el ticket promedio entre clientes `Particulares` y clientes de tipo `Empresa`,  y como se encuentra con respecto al onjetivo de ticket promedio de clientes `Particulares`?
5. - ¿Qué métodos de pago prefieren los clientes y cómo se alinea esto al objetivo de pagos digitales de la empresa?

## Guía de Instalación y Ejecución

1. ****Clonar el repositorio o descargar el proyecto:****Bash

   git clone
   cd TechData
2. ****Crear y activar un entorno virtual:****Bash

   python -m venv venv\# En Windows:venv\\Scripts\\activate\# En Mac/Linux:source venv/bin/activate
3. ****Instalar las dependencias:****Bash

   pip install -r requirements.txt
4. ****Configurar las variables de entorno:**** Crea un archivo `.env` en la raíz del proyecto con las credenciales de tu base de datos PostgreSQL:Fragmento de código

   DB\_USER="tu\_usuario"DB\_PASSWORD="tu\_contraseña"DB\_HOST="tu\_host"DB\_PORT=5432DB\_NAME="nombre\_base\_de\_datos"DB\_SSLMODE="require"
5. ****Ejecutar el Pipeline ETL:****
   Bash

   python tecnologia.py

   __Esto limpiará el dataset crudo, generará el archivo__ _`_dataset_limpio_tienda_tecnologia.csv_`___, construirá el modelo dimensional y poblará automáticamente las tablas relacionales en la base de datos PostgreSQL.__

__Desarrollado para TechData — Análisis de Sistemas y Business Intelligence.__

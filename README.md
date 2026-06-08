# Polla Mundial 2026 - App en Streamlit

Aplicación simple para un concurso recreativo de pronósticos del Mundial 2026.

## Archivos

- `app.py`: aplicación principal.
- `fixture.csv`: fixture de 104 partidos.
- `requirements.txt`: librerías necesarias.
- `.streamlit/config.toml`: configuración visual.

## Cómo ejecutarlo en Visual Studio Code

1. Abre Visual Studio Code.
2. Crea una carpeta, por ejemplo: `polla_mundial_2026`.
3. Copia dentro todos estos archivos.
4. Abre una terminal en esa carpeta.
5. Instala las librerías:

```bash
pip install -r requirements.txt
```

6. Ejecuta la app:

```bash
streamlit run app.py
```

7. Se abrirá en el navegador.

## Código de administrador

Por defecto es:

```text
admin2026
```

Puedes cambiarlo antes de publicar usando una variable de entorno:

```bash
ADMIN_CODE=otro_codigo streamlit run app.py
```

En Windows PowerShell:

```powershell
$env:ADMIN_CODE="otro_codigo"
streamlit run app.py
```

## Publicación en internet

Para una versión rápida, puedes subir estos archivos a GitHub y desplegar en Streamlit Community Cloud.

Para una versión más estable con base de datos persistente, conviene Render o Railway con almacenamiento persistente o una base externa.

## Nota importante

Esta versión usa SQLite local: crea el archivo `polla_mundial_2026.db` automáticamente cuando se ejecuta.
Si lo publicas en una nube gratuita sin disco persistente, los datos podrían perderse al reiniciarse la app.


## Acceso oculto al administrador

En la versión mundialista, el menú de Administrador no aparece para los participantes.

Para verlo, abre la app agregando `?admin=1` al final del enlace.

Ejemplo local:

```text
http://localhost:8501?admin=1
```

Ejemplo publicado:

```text
https://tu-app.streamlit.app?admin=1
```

Luego usa el código de administrador:

```text
admin2026
```



## Banderas reales

Esta versión usa imágenes reales de banderas desde `flagcdn.com`, para evitar que en Windows o algunos navegadores aparezcan banderas blancas en lugar del país correspondiente.

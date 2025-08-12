import os
import io
import sys
import subprocess  # Módulo para ejecutar comandos del sistema
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from orgparse import load

# Define los alcances (scopes) de la API
SCOPES = ['https://www.googleapis.com/auth/blogger']
# ID de tu blog
BLOG_ID = '4324169104029630098'


def get_credentials():
    """Obtiene y refresca las credenciales de la API."""
    creds = None
    if os.path.exists('config/token.json'):
        creds = Credentials.from_authorized_user_file('config/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'config/client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('config/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def read_and_convert_org_file(org_file_path):
    """
    Exporta un archivo .org a .html usando Emacs y luego lee los metadatos.
    """
    html_file_path = org_file_path.replace('.org', '.html')

    try:
        # --- NUEVA LÓGICA: Ejecutar Emacs para exportar el archivo ---
        emacs_command = [
            'emacs',
            '--batch',
            '--eval',
            f'(progn (find-file "{org_file_path}") (org-html-export-to-html))'
        ]

        print("Exportando archivo .org a .html con Emacs...")
        subprocess.run(emacs_command, check=True, capture_output=True, text=True)
        print("Exportación de Emacs completada.")

        # Leer los metadatos del archivo .org original con orgparse
        org_document = load(org_file_path)
        post_title = org_document.get_file_property("title")
        tags_string = org_document.get_file_property("tags")

        if tags_string:
            post_labels = [tag.strip() for tag in tags_string.split(',')]
        else:
            post_labels = []

        # Leer el contenido HTML generado por Emacs
        with io.open(html_file_path, 'r', encoding='utf-8') as f:
            post_content_html = f.read()

        return post_title, post_content_html, post_labels
    except FileNotFoundError:
        print("Error: No se encontró el comando 'emacs' o los archivos.")
        return None, None, None
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar Emacs: {e.stderr}")
        return None, None, None
    except Exception as e:
        print(f"Error al procesar el archivo Org-mode: {e}")
        return None, None, None


def create_blogger_post(blog_id, title, content, labels):
    """Crea y publica un post en Blogger."""
    creds = get_credentials()
    try:
        service = build('blogger', 'v3', credentials=creds)
        post_body = {
            'kind': 'blogger#post',
            'blog': {'id': blog_id},
            'title': title,
            'content': content,
            'labels': labels
        }
        response = service.posts().insert(blogId=blog_id, body=post_body, isDraft=False).execute()
        print(f"Post creado exitosamente. Título: {response['title']}")
        print(f"URL del post: {response['url']}")
    except HttpError as error:
        print(f"Ha ocurrido un error al crear el post: {error}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python publicar_en_blogger.py <nombre_del_archivo.org>")
        sys.exit(1)

    org_file_name = sys.argv[1]
    org_file_path = os.path.join('posts_org', org_file_name)
    html_file_path = org_file_path.replace('.org', '.html')

    post_title, post_content, post_labels = read_and_convert_org_file(org_file_path)

    if post_title and post_content:
        success = create_blogger_post(BLOG_ID, post_title, post_content, post_labels)

        # --- NUEVA LÓGICA: Elimina el archivo solo si la publicación fue exitosa ---
        if success and os.path.exists(html_file_path):
            os.remove(html_file_path)
            print(f"Archivo temporal '{html_file_path}' eliminado.")

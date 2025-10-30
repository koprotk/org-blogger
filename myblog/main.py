import os
import io
import sys
import subprocess
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from orgparse import load

# Define los alcances (scopes) de la API
SCOPES = ['https://www.googleapis.com/auth/blogger']

def get_credentials(cred_dir):
    """Obtiene y refresca las credenciales de la API."""
    creds = None
    token_dir = os.path.join(cred_dir, 'token.json')
    secret_dir = os.path.join(cred_dir, 'client_secret.json')
    if os.path.exists(token_dir):
        creds = Credentials.from_authorized_user_file(token_dir, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                secret_dir, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_dir, 'w') as token:
            token.write(creds.to_json())
    return creds

def get_my_blog_id(cred_dir):
    """Obtiene el ID del blog del usuario autenticado."""
    creds = get_credentials(cred_dir)  
    service = build('blogger', 'v3', credentials=creds)
    blogs = service.blogs().listByUser(userId='self').execute()
    if 'items' in blogs and blogs['items']:
        blog_id = blogs['items'][0]['id']
        print(f"Your blog ID is: {blog_id}")
        return blog_id
    else:
        print("No blogs found for this user.")
        return None


def export_and_read_files(org_file_path):
    """Exporta un archivo .org a .html con Emacs y lee los metadatos y el contenido."""
    html_file_path = org_file_path.replace('.org', '.html')

    try:
        # 1. Exporta el archivo .org a .html con Emacs
        emacs_command = [
            'emacs',
            '--batch',
            '--eval',
            f'(progn (find-file "{org_file_path}") (org-html-export-to-html))'
        ]

        print("Exportando archivo .org a .html con Emacs...")
        subprocess.run(emacs_command, check=True, capture_output=True, text=True)
        print("Exportación de Emacs completada.")

        # 2. Lee los metadatos y el contenido
        org_document = load(org_file_path)
        post_title = org_document.get_file_property("title")
        tags_string = org_document.get_file_property("tags")

        if tags_string:
            post_labels = [tag.strip() for tag in tags_string.split(',')]
        else:
            post_labels = []

        with io.open(html_file_path, 'r', encoding='utf-8') as f:
            post_content_html = f.read()

        return post_title, post_content_html, post_labels
    except Exception as e:
        print(f"Ha ocurrido un error durante la exportación o lectura de archivos: {e}")
        return None, None, None


def create_blogger_post(blog_id, title, content, labels, cred_dir):
    """Crea y publica un post en Blogger."""
    creds = get_credentials(cred_dir)
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
        return True
    except HttpError as error:
        print(f"Ha ocurrido un error al crear el post: {error}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python publicar_en_blogger.py <nombre_del_archivo.org>")
        sys.exit(1)

    org_file_name = sys.argv[1]
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    drafts_dir = os.path.join(base_dir, 'drafts')
    posts_dir = os.path.join(base_dir, 'posts')
    cred_dir = os.path.join(base_dir, 'config')

    org_file_path = os.path.join(drafts_dir, org_file_name)
    html_file_path = org_file_path.replace('.org', '.html')

    if not os.path.exists(org_file_path):
        print(f"Error: El archivo '{org_file_path}' no se encontró.")
        sys.exit(1)

    if os.path.isdir(org_file_path):
        print(f"Error: '{org_file_path}' es una carpeta, se esperaba un archivo.")
        sys.exit(1)

    post_title, post_content, post_labels = export_and_read_files(org_file_path)

    if post_title and post_content:
        BLOG_ID = get_my_blog_id(cred_dir)
        success = create_blogger_post(BLOG_ID, post_title, post_content, post_labels, cred_dir)

        if success:
            posted_file_path = os.path.join(posts_dir, org_file_name)

            try:
                # Mueve el archivo de 'drafts' a 'posts'
                os.rename(org_file_path, posted_file_path)
                print(f"Archivo '{org_file_name}' movido de 'drafts' a 'posts'.")
            except OSError as e:
                print(f"Error al mover/renombrar el archivo: {e}")

        if os.path.exists(html_file_path):
            os.remove(html_file_path)
            print(f"Archivo temporal '{html_file_path}' eliminado.")

if __name__ == '__main__':
    main()
    

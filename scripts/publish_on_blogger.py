import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define los alcances (scopes) de la API
SCOPES = ['https://www.googleapis.com/auth/blogger']

# ID de tu blog. Puedes encontrarlo en la URL de tu panel de Blogger.
# Ejemplo: "https://www.blogger.com/blog/posts/XXXXXXXXXXXXX"
BLOG_ID = '4324169104029630098'


def main():
    """Muestra cómo subir un post a Blogger."""
    creds = None

    # El archivo token.json almacena los tokens de acceso y refresco del usuario
    # y se crea automáticamente la primera vez que se completa el flujo de autorización.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Si no hay credenciales válidas disponibles, inicia el flujo de inicio de sesión.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Guarda las credenciales para futuras ejecuciones.
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Construye el objeto de servicio de la API de Blogger
        service = build('blogger', 'v3', credentials=creds)

        # Define el contenido de la publicación
        post_body = {
            'kind': 'blogger#post',
            'blog': {
                'id': BLOG_ID
            },
            'title': 'Mi primer post con la API de Python',
            'content': 'Este es un post de ejemplo publicado automáticamente usando la API de Blogger con Python. ¡Es genial!',
            'labels': ['python', 'api', 'programacion']
        }

        # Realiza la llamada a la API para insertar el post
        response = service.posts().insert(blogId=BLOG_ID, body=post_body, isDraft=False).execute()

        print(f"Post creado exitosamente. Título: {response['title']}")
        print(f"URL del post: {response['url']}")

    except HttpError as error:
        print(f"Ha ocurrido un error: {error}")


if __name__ == '__main__':
    main()

from __future__ import print_function
import mysql.connector
import pickle
import os
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from tabulate import tabulate 
from googleapiclient import errors
import mimetypes
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import base64
from apiclient import errors, discovery
import httplib2
import oauth2client
from oauth2client import client, tools, file
from base64 import b64encode
from base64 import b64decode
import unittest

# Conectamos con MySQL

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=""
)

mycursor = mydb.cursor()

# Creamos la base de datos "googledrive" donde estaran almacenados los archivos

mycursor.execute("CREATE DATABASE googledrive")

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="googledrive"
)

mycursor = mydb.cursor()

# Creamos dos tablas: "archivos" y "archivospublicos". Dentro de "archivos" estaran todos los archivos de Google Drive.
# Dentro de "archivospublicos" se encontraran los archivos que alguna vez fueron publicos.

mycursor.execute("CREATE TABLE archivos (idArchivo VARCHAR(255), nombreArchivo VARCHAR(255), extension VARCHAR(255), owner VARCHAR(255), esCompartido VARCHAR(255), fechaModificacion VARCHAR(255), PRIMARY KEY(idArchivo))")

mycursor.execute("CREATE TABLE archivospublicos (idArchivo VARCHAR(255), nombreArchivo VARCHAR(255), extension VARCHAR(255), owner VARCHAR(255), fechaModificacion VARCHAR(255), PRIMARY KEY(idArchivo))")

# Se realiza el INSERT en MySQL de todos los archivos que se encuentran en Google Drive

def insertFilesIntoTable(items):

    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='googledrive',
                                             user='root',
                                             password='')
        cursor = connection.cursor()

        for item in items:
            item["id"]
            item["name"]
            item["mimeType"]
            item['owners'][0]['emailAddress']
            item["shared"]
            item["modifiedTime"]
            cursor.execute(""" INSERT INTO archivos (idArchivo, nombreArchivo, extension, owner, esCompartido, fechaModificacion) VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE nombreArchivo=%s, extension=%s, owner=%s, esCompartido=%s, fechaModificacion=%s""", (item["id"],item["name"],item["mimeType"],item['owners'][0]['emailAddress'],item["shared"],item["modifiedTime"],item["name"],item["mimeType"],item['owners'][0]['emailAddress'],item["shared"],item["modifiedTime"]))
            connection.commit()
            print("Record inserted successfully into archivos table")

    except mysql.connector.Error as error:
            print("Failed to insert into MySQL table {}".format(error))

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")   
    
# Se realiza el INSERT en MySQL de los archivos que fueron publicos en algun momento, que se encuentran en Google Drive

def insertFilePublicIntoTable(id, name, mime_type, owners, modified_time):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='googledrive',
                                             user='root',
                                             password='')
        cursor = connection.cursor()
        mySql_insert_query = """INSERT INTO archivospublicos (idArchivo, nombreArchivo, extension, owner, fechaModificacion) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE nombreArchivo=%s, extension=%s, owner=%s, fechaModificacion=%s""" 

        recordTuple = (id, name, mime_type, owners, modified_time, name, mime_type, owners, modified_time)
        cursor.execute(mySql_insert_query, recordTuple)
        connection.commit()
        print("Record inserted successfully into archivospublicos table")

    except mysql.connector.Error as error:
        print("Failed to insert into MySQL table {}".format(error))

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

# Scopes: Autorizaciones para realizar distintas operaciones dentro de Google Drive y Gmail.
# En caso de modificar estos scopes, se debe eliminar el archivo token.pickle / gmailtoken.pickle
SCOPES = ['https://www.googleapis.com/auth/drive']
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Obtenemos el servicio de Google Drive

def get_gdrive_service():
    creds = None
    # El archivo token.pickle guarda access y refresh token del usuario, y se crea automaticamente una vez que
    # realicemos el workflow de autenticacion por primera vez.
    if os.path.exists('drivetoken.pickle'):
        with open('drivetoken.pickle', 'rb') as token:
            creds = pickle.load(token)
    # Si no hay credenciales o no son validas, deja al usuario ingresar.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'drivecredentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Se guardan las credenciales para la proxima corrida
        with open('drivetoken.pickle', 'wb') as token:
            pickle.dump(creds, token)
    # Devuelve el servicio de Google Drive
    return build('drive', 'v3', credentials=creds)

# Obtenemos el servicio de Gmail

def get_gmail_credentials():
    
    creds = None
    # El archivo token.pickle guarda access y refresh token del usuario, y se crea automaticamente una vez que
    # realicemos el workflow de autenticacion por primera vez.
    if os.path.exists('gmailtoken.pickle'):
        with open('gmailtoken.pickle', 'rb') as token:
            creds = pickle.load(token)
    # Si no hay credenciales o no son validas deja al usuario ingresar.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'gmailcredentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Se guardan las credenciales para la proxima corrida.
        with open('gmailtoken.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# Removemos un permiso

def remove_permission(service, file_id, permission_id):

  try:
    service.permissions().delete(
        fileId=file_id, permissionId=permission_id).execute()
  except errors.HttpError as error:
    print ('An error occurred: %s' % error)

# Creamos el mail que sera enviado via Gmail

def create_message(sender, to, subject, message_text):

  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw' : base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('ascii')} 

# Enviamos el mail via Gmail

def send_message(service, user_id, message):

  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print ('Message Id: %s' % message['id'])
    return message
  except errors.HttpError as error:
    print ('An error occurred: %s' % error) 

def main():

    service = get_gdrive_service()
    gmailservice = get_gmail_credentials()
    # Llamamos a la API de Google Drive para que nos traiga campos que necesitamos de cada archivo
    results = service.files().list(
        pageSize=8, fields="nextPageToken, files(name, id, mimeType, owners/emailAddress, owners/permissionId, shared, modifiedTime)").execute()
    # Realizamos un get de los resultados
    items = results.get('files', [])
    # Definimos una variable para cada campo
    for item in items :
         # ID del Archivo
         idArchivo = item["id"]
         # Nombre del Archivo
         nombreArchivo = item["name"]
         # Extension (Mime Type) del archivo
         extension = item["mimeType"]
         # ID del Owner del archivo
         ownerId = item['owners'][0]['permissionId']
         # Email del owner del archivo
         ownerEmail = item['owners'][0]['emailAddress']
         # Si es Compartido. En caso de ser TRUE, el archivo es Compartido/Publico, en caso de ser FALSE el archivo no esta Compartido / es Privado.
         shared = item["shared"]
         # Fecha de Modificacion del archivo.
         fechaModificacion = item["modifiedTime"]
         if shared == True :
            insertFilePublicIntoTable(idArchivo,nombreArchivo,extension,ownerEmail,fechaModificacion)
            # Llamamos a la API de Google Drive para que nos traiga los ID de los permisos que hay en cada archivo.
            resultados = service.permissions().list(pageSize=8, fileId=idArchivo, fields="nextPageToken, permissions(id)").execute()
            # Realizamos un get de los resultados
            permisos = resultados.get('permissions', [])
            # Definimos la variable idPermiso
            for permiso in permisos :
                idPermiso = permiso["id"]
                # Comparamos los ID de los permisos que hay en el archivo con el ID del Owner del archivo.
                if idPermiso != ownerId :
                    # En caso de que el ID del permiso sea distinto al ID del owner, se remueve el permiso.
                    remove_permission(service,idArchivo,idPermiso)
                    # Llamamos a la API de Gmail y creamos el mail de notificacion al Owner del Archivo.
                    message = create_message("me", (ownerEmail), 'Se convirtio a Privado un archivo suyo en Google Drive', (nombreArchivo))
                    # Se envia el mail de notificacion
                    send_message(gmailservice, "me", message)
    
    # Realizamos nuevamente el get de los archivos en caso de que se haya eliminado algun permiso.
    items = results.get('files', [])
    # Insertamos los archivos en la base de datos.
    insertFilesIntoTable(items)

if __name__ == '__main__':
    main()

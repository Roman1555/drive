from __future__ import print_function
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import logging

import os.path

import google.auth
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError





TOKEN = '6538295187:AAFooJcZhI6xhr5cILcBLAz90wg15L0pn1U'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO, #print level(all info)
    filename='pylog.log',
    filemode='w'
)
#add a logging 

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f'message')
    await update.message.reply_text(text=f'Hello {update.effective_user.first_name}')



def creds():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    #"https://www.googleapis.com/auth/drive.metadata.readonly"
    SCOPES = ['https://www.googleapis.com/auth/drive']
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
        )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds



async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        service = build("drive", "v3", credentials=creds())

        # Call the Drive v3 API
        results = (
            service.files()
            .list(pageSize=10, fields="nextPageToken, files(id, name)")
            .execute()
        )
        items = results.get("files", [])

        if not items:
            print("No files found.")
            return
        
        s = ''
        for item in items:
            s += f"{str(item.get('name'))}\n"
        print("Files:")
        for item in items:
            print(f"{item['name']} ({item['id']})")
        await update.message.reply_text(text=s)
        
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")
    

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_file = await update.message.effective_attachment.get_file()
    await new_file.download_to_drive(custom_path='downloaded/'+update.message.effective_attachment.file_name)
#update.message.effective_attachment.file_name
    """Insert new file.
    Returns : Id's of the file uploaded

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """


    try:
        # create drive api client
        service = build("drive", "v3", credentials=creds())

        file_metadata = {"name": update.message.document.file_name}
        media = MediaFileUpload('downloaded/'+update.message.document.file_name,
                                    mimetype=update.message.document.mime_type, resumable=True)
            # pylint: disable=maybe-no-member
            ######
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
            )
        print(f'File ID: {file.get("id")}')

    except HttpError as error:
    #     #failure
        await update.message.reply_text(text='Failure')
        print(f"An error occurred: {error}")
        file = None
    #success
    await update.message.reply_text(text='Success')

    return file.get("id")





if __name__ == '__main__':

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', hello))
    app.add_handler(CommandHandler('hello', hello))
    app.add_handler(CommandHandler('files', list_files))
    app.add_handler(MessageHandler(filters.Document.ALL, upload))

    app.run_polling()


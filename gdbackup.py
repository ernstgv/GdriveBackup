from __future__ import print_function
import os, time, datetime, sys
from datetime import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


def main():

    ## Taking inputs for the location of Gdrive directory, local PC directory ETC.

    print('')
    GdriveBackupFolder = input('Enter the Gdrive folder. Must already EXIST in the top most level: ')

    print('')
    LocalDirectoryToBeBackup = input('Local Directory to be Backup: ').replace("\\", "/")

    print('')
    InputDate = input('First Run... Please Enter a Date OF FILES to be uploaded in GDrive in MM/DD/YYYY format: ')

    print('')
    DateFormat = '%m/%d/%Y'

    FileTimeStamp = int(time.mktime(time.strptime(InputDate, DateFormat)))

    HowFrequent = int(input('Every how many hours you want the backup to run: '))

    SleepTime = HowFrequent * 3600
    print('')
    print('Cool, will start now!!!')
    print('')


    while True:

        SessionRunTime = datetime.now()
        SessionRunTimemessage = SessionRunTime.strftime("%d-%b-%Y (%H:%M:%S.%f)")
        print('Session Runtime', SessionRunTimemessage)
        print('')

        # THE AUTHENTICATION PART CAME FROM GOOGLE DRIVE API QUICKSTART TEMPLATE
        # This is None below is just to initialize the creds to NULL value
        creds = None

        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user complete the log in screen.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        ## This is the end of authentication part
        
        # Instantiating gdrive
        gdrive = build('drive', 'v3', credentials=creds)


        ## FINDING OUT THE FILEID OF GdriveBackupFolder that was asked earlier
        print('Backing Up in', GdriveBackupFolder)
        print('')

        GdriveBackupFoldersearchquery = "name = '{}'".format(GdriveBackupFolder)

        GdriveBackupFolderMatchedItem = gdrive.files().list(q = GdriveBackupFoldersearchquery, fields="files(id)").execute()
                        
        GdriveBackupFolderMatchingFileId = GdriveBackupFolderMatchedItem.get('files', [])

        GdriveBackupFolderMatchedItemFinalMatchingId = GdriveBackupFolderMatchingFileId[0]['id']

        ## FILEID OF GDRIVEBACKUP FOLDER is now FOUND


        ## ENUMERATING FILES THAT EXIST IN GDRIVEBACKUP FOLDER FOR COMPARISON WITH LOCAL DIRECTORY

        SearchQueryForResults = "'{}' in parents".format(GdriveBackupFolderMatchedItemFinalMatchingId)

        results = gdrive.files().list(q = SearchQueryForResults, pageSize=10, 
                                        fields="nextPageToken, files(name)").execute()

        items = results.get('files', [])

        gdrivefilelist = []

        for item in items:

            gdrivefilelist.append(item['name'])
        
        ## FILES' LIST IS NOW IN LIST, gdrivefilelist


        ## GENERATING FILES from the local PC directory TO BE UPLOADED TO GDRIVE.
        
        print('Files in Local directory that needs to be uploaded/updated')        
            
        ## building up the files, filelist = [],  that needs upload. This is from local PC drive.
        filelist = []

        for uploadfile in os.listdir(LocalDirectoryToBeBackup):

            filetocompare = os.path.join(LocalDirectoryToBeBackup, uploadfile).replace("\\", "/")    ###  .replace("\\", "/") is for mixed windows path.

            if os.path.getmtime(filetocompare) > FileTimeStamp:

                if os.path.isfile(filetocompare):

                    print('  ',uploadfile)
                    filelist.append(uploadfile)
        
        if not filelist:
            print('   No files for upload or update is found, Skipping for now...')
            print('')

        
        ## CONTINUE WITH UPLOADING FILES IF THERE ARE ANY LOCAL FILES TO BE UPLOADED OR UPDATED.
        else:

            print('')
            for filelistitem in filelist:

                ### Comparing Gdrive and local. THIS IS IMPORTANT TO DO BECAUSE EVEN "UPDATE" WILL UPLOAD A NEW FILE IF FILEID IS NOT SPECIFIED.
                ## upload if file is not in Gdrive
                if filelistitem not in gdrivefilelist:
                    print('  ', filelistitem, 'will be uploaded')

                    fileforupload = os.path.join(LocalDirectoryToBeBackup, filelistitem).replace("\\", "/") 

                    destination_metadata = {'name': filelistitem, 'parents' : [GdriveBackupFolderMatchedItemFinalMatchingId]}

                    mediaBody = MediaFileUpload(fileforupload)

                    FileUploadAction = gdrive.files().create(body=destination_metadata,
                                                        media_body=mediaBody,
                                                        fields='id').execute()

                    print('      Done uploading', filelistitem)

                    ## END of UPLOADING ACTION


                ## Update if files are already in Gdrive. IF FILEID IS NOT SPECIFIED, A NEW FILE OF SAME NAME WILL BE UPLOADED.
                if filelistitem in gdrivefilelist:
                    print('  ',filelistitem, 'will be updated')

                    ## get the fileID of the file matching file

                    searchquery = "name = '{0}' and '{1}' in parents".format(filelistitem, GdriveBackupFolderMatchedItemFinalMatchingId)            

                    matcheditem = gdrive.files().list(q = searchquery, fields="files(id)").execute()
                    
                    matchingfileid = matcheditem.get('files', [])

                    ## a case of list inside a list?
                    finalmatchingid = matchingfileid[0]['id']

                    destination_metadata = {'name': filelistitem}

                    fileforupload = os.path.join(LocalDirectoryToBeBackup, filelistitem).replace("\\", "/")

                    mediaBody = MediaFileUpload(fileforupload)

                    FileUpdateAction = gdrive.files().update(fileId=finalmatchingid, body=destination_metadata,
                                                        media_body=mediaBody,
                                                        addParents=GdriveBackupFolderMatchedItemFinalMatchingId,
                                                        fields='id').execute()

                    print('      Done Updating', filelistitem)

                    # END OF UPDATING ACTION

            print('')

        ## DISPLAYING THE FILES IN GDRIVE

        listing_confirmation = gdrive.files().list(q = SearchQueryForResults, pageSize=10, fields="nextPageToken, files(id, name, modifiedTime)").execute()

        listings2 = listing_confirmation.get('files', [])

        if not listings2:
            print('No files found.')
        else:
            print('Files Currently in GDrive',GdriveBackupFolder)
            for listing2 in listings2:
                print(u'   {0} {1} {2}'.format(listing2['name'], listing2['id'], listing2['modifiedTime']))

        ## End of DISPLAYING THE FILES IN GDRIVE


        # FileTimeStamp JUST GOT CARRIED FROM PREVIOUS DEVELOPMENT
        # THIS SECTION WILL JUST SET THE NEW TIMESTAMP FOR THE STARTING WHILE LOOP -> HowFrequent
        FileTimeStamp = datetime.now().timestamp()

        print('')

        print('Sleeping for', HowFrequent, 'HRS...')
        print('-------------------------------------')
        
        time.sleep(SleepTime)


# this is just to call the program starting point.
if __name__ == '__main__':
    main()

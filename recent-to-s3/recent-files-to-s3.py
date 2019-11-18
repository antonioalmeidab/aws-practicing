import os
from datetime import datetime
import boto3
s3 = boto3.resource('s3')

def latest_modified_files(target_directory, time_range):
    now = datetime.now().timestamp()
    files = []

    for root, _, filenames in os.walk(target_directory, topdown=False):
        for name in filenames:
            file_path = os.path.join(root, name)
            last_modified_date = os.path.getmtime(file_path)
            time_gap = (now - last_modified_date)/3600
            
            if time_gap < time_range:
                files.append(
                    {
                        'file' : file_path,
                        'key': file_path.replace(target_directory+'/', '')
                    }
                )
    return files

def recent_files_to_s3bucket(directory, bucket_name, time_range, s3_resource):
    files = latest_modified_files(directory, time_range)

    now = str(datetime.now()).split(' ')
    current_date = now[0]
    current_time = now[1][:8]

    for file in files:
        s3_resource.meta.client.upload_file(
            file['file'],
            bucket_name,
            current_date+'/'+current_time+'/'+file['key']
        )

def main():
    recent_files_to_s3bucket(
        '/home/antonio/Documentos/pasta-teste',
        'antonio4a181673429f0b6abbfd452f0f3b5950',
        6,
        s3
    )

if __name__ == "__main__":
    main()
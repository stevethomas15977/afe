import os

def write_to_file(file_path, content):
    # Open the file in append mode, create it if it doesn't exist, and write the content
    with open(file_path, 'w+') as file:
        file.write(content)



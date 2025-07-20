import os

# Define the target folder
folder_path = r"C:\Users\yigit\Documents\repos\Youtube-playlist-to-formatted-text\cs224w_machine learning with graphs"

# List all .txt files in the folder
txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

# Sort the file names
txt_files.sort()

# Print the sorted list
for idx, file_name in enumerate(txt_files, 1):
    print(f"{idx}. {file_name}")

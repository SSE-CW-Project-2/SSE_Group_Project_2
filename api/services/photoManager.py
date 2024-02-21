####################################################################################################
# Project Name: Motive Event Management System
# Course: COMP70025 - Software Systems Engineering
# File: photoManager.py
# Description: This file contains the flask routes to upload and fetch photos to display on a venue
#              or artist's home page.
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-02-21
# Version: 1.0
#
# Changes: Created.
#
# Notes: JS partial code to upload and retrieve photos included at the end of the file.
####################################################################################################


from flask import Flask, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Supabase setup
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_PRIVATE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route('/upload', methods=['POST'])
def upload_photo():
    # # Authenticate the user and get user_id if necessary
    # user_id, error = authenticate(request)
    # if error:
    #     return jsonify({'error': error}), 401
    user_id = request.args.get('user_id')

    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    # Organize uploads by user_id
    file_path = f"uploads/{user_id}/{file.filename}"

    # Upload to Supabase
    response = supabase.storage.from_('profile-photos').upload(file_path, file)

    if response.get('error') is None:
        public_url = supabase.storage.from_('profile-photos').get_public_url(file_path).data.get('publicURL')

        # Insert URL into images table to more easily associate photos with user IDs
        db_insert_result = supabase.table('images').insert({'url': public_url, 'user_id': user_id}).execute()

        return jsonify({'url': public_url}), 200
    else:
        return jsonify({'error': response['error']['message']}), 500


@app.route('/get-images', methods=['GET'])
def get_images():
    # Note: Have assumed so far that we want to store/filter by user_id
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    # Fetch images filtered by user_id
    response = supabase.table("images").select("*").eq("user_id", user_id).execute()

    if response.error:
        return jsonify({'error': response.error.message}), 500
    else:
        image_urls = [row['url'] for row in response.data]
        return jsonify(image_urls), 200


if __name__ == '__main__':
    app.run(debug=True)


####################################################################################################
# JS placeholder to upload a photo - needs tweaking and design decisions
# --------------------------------------------------------------------------------------------------
# < input
# type = "file"
# id = "photoInput"
# accept = "image/*" >
# < button
# onclick = "uploadPhoto()" > Upload
# Photo < / button >
#
# < script >
# async function
# uploadPhoto()
# {
#     const
# fileInput = document.getElementById('photoInput');
# const
# file = fileInput.files[0];
#
# if (!file)
# {
#     alert('Please select a file to upload.');
# return;
# }
#
# userId = getCurrentUserId(); // Implement
# const photoType = 'profile';
#  const formData = new FormData();
#     formData.append('file', file);
#     formData.append('user_id', userId); // Need to decide how to pass user_id
#     formData.append('photo_type', photoType);
#
#     try {
#         const response = await fetch('http://localhost:5000/upload', {
#             method: 'POST',
#             body: formData, // automatically set to 'multipart/form-data'
#         });
#
#         if (response.ok) {
#             const result = await response.json();
#             console.log('Upload successful:', result.url);
#             alert('Upload successful!');
#         } else {
#             throw new Error('Upload failed');
#         }
#     } catch (error) {
#         console.error('Error uploading photo:', error);
#         alert(error.message);
#     }
# }
#
# </script>
####################################################################################################

####################################################################################################
# Clientside JS placeholder to retrieve a user's photos - needs tweaking and design decisions
# --------------------------------------------------------------------------------------------------
# const userId = 'your_user_id_here'; // Need a mechanism to retrieve this
# fetch(`http://localhost:5000/get-images?user_id=${userId}`) // ChatGPT suggested this
#     .then(response => response.json())
#     .then(urls => {
#         const container = document.getElementById('photos-container');
#         urls.forEach(url => {
#             const img = document.createElement('img');
#             img.src = url;
#             // Define styling here
#             img.style.width = '100px';
#             img.style.height = '100px';
#             img.alt = 'Photo';
#             container.appendChild(img);
#         });
#     })
#     .catch(error => console.error('Error fetching images:', error));
#
####################################################################################################
import os
import cv2
import numpy as np
import tensorflow as tf

# Load the saved model
model = tf.keras.models.load_model('tumor_detection_model.h5')
print("Model loaded successfully.")

# Function to preprocess and predict a new image
def predict_tumor(image_path):
    # Check if the file exists
    if not os.path.isfile(image_path):
        print(f"Error: File does not exist at path: {image_path}")
        return
    
    image_size = 128  # Same size as used in training
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Load image as grayscale
    
    if img is None:
        print(f"Error: Unable to load image at path: {image_path}")
        return
    
    img = cv2.resize(img, (image_size, image_size))  # Resize to 128x128
    img = img / 255.0  # Normalize
    img = np.expand_dims(img, axis=-1)  # Add channel dimension
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    
    # Predict using the loaded model
    prediction = model.predict(img)
    predicted_class = np.argmax(prediction, axis=1)
    
    if predicted_class == 0:
        print("Prediction: Tumorous Brain")
    else:
        print("Prediction: Non-tumorous Brain")

# Path to directory containing images
directory_path = r'D:\both tumor and not'  # Use raw string to avoid issues with backslashes

# List all files in the directory
try:
    files = os.listdir(directory_path)
    print(f"Files in directory {directory_path}:")
    for file_name in files:
        print(file_name)

    # Use the first image file for prediction (replace this with the specific file you want)
    if files:
        first_image_path = os.path.join(directory_path, files[0])
        print(f"Attempting to load image from: {first_image_path}")
        predict_tumor(first_image_path)
    else:
        print(f"No files found in directory: {directory_path}")

except Exception as e:
    print(f"Error accessing directory: {e}")

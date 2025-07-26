import os
import openai
import subprocess
import speech_recognition as sr
import pyttsx3
import requests
import json
import webbrowser
import urllib.parse
from googleapiclient.discovery import build
from time import sleep
from datetime import datetime
import string
import wikipedia

# Set your OpenAI API key
openai.api_key = ""

# YouTube API key
youtube_api_key = ""

# Fast2SMS API key
fast2sms_api_key = ""

# Emergency contacts
emergency_contacts = ['']  # Replace with your loved ones' phone numbers

esp32_url = "https://192.168.48.222/distance"

# Initialize text-to-speech engine
engine = pyttsx3.init()

def configure_voice():
    voices = engine.getProperty('voices')
    preferred_voice_index = 1  # Update this index based on the listed voices
    engine.setProperty('voice', voices[preferred_voice_index].id)
    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1.0)

# Set up the voice before any speech is spoken
configure_voice()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        print("Recognizing speech...")
        query = recognizer.recognize_google(audio)
        print(f"You said: {query}")
        return query.lower()
    except sr.UnknownValueError:
        print("Sorry, I didn't understand that.")
        return ""
    except sr.RequestError:
        print("Sorry, the speech service is down.")
        return ""

def greet_boss():
    hour = datetime.now().hour

    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    speak(f"{greeting}, Boss. How are you? What's the task today?")
def launch_application(app_name):
    app_name = app_name.lower().strip()

    if app_name in apps:
        try:
            # Use os.startfile for simplicity
            os.startfile(apps[app_name])
            # Speak removed to avoid file path announcement
            # speak(f"Launching {app_name}.")
        except FileNotFoundError:
            speak(f"Could not find the application {app_name}. Please check its installation.")
        except Exception as e:
            speak(f"An error occurred while launching {app_name}: {str(e)}")
    else:
        speak(f"Sorry, I don't know how to launch {app_name}. Please add it to my list.") 

apps = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "vscode": "C:\\Users\\YourUsername\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
    "word": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
    "excel": "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE",
    "powerpoint": "C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE",
    "cmd": "cmd.exe",
    "explorer": "explorer.exe",
    

}    
def get_distance():
    try:
        response = requests.get(esp32_url)
        data = response.json()
        distance = data.get('distance', None)
        return distance
    except Exception as e:
        print(f"Error getting distance from ESP32: {str(e)}")
        return None


def send_sos_message():
    message = "THIS MESSAGE IS FROM NEURA (AI ASSISTANT) SAFWAN IN EMERGENCY CALL HIM"
    url = "https://www.fast2sms.com/dev/bulkV2"

    payload = {
        "route": "q",
        "message": message,
        "flash": 0,
        "numbers": ','.join(emergency_contacts),
    }

    headers = {
        "authorization": fast2sms_api_key,
        "Content-Type": "application/json"
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        print(f"SOS message sent: {response.text}")
        speak("SOS message sent to your loved ones.")
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")
        speak("Failed to send SOS message.")

def ask_neura(conversation):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation,
            max_tokens=100,
            temperature=0.9,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"

def open_website(website_name):
    url = f"https://www.{website_name}.com"
    print(f"Opening {website_name}...")
    webbrowser.open(url)
    speak(f"Opening {website_name}")

def play_song(song_name):
    youtube = build('youtube', 'v3', developerKey=youtube_api_key)

    search_request = youtube.search().list(
        q=song_name,
        part="snippet",
        maxResults=1
    )

    search_response = search_request.execute()

    if search_response["items"]:
        video_id = search_response["items"][0]["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        print(f"Playing song: {song_name}")
        webbrowser.open(video_url)
        speak(f"Playing {song_name} on YouTube.")
    else:
        print(f"Could not find the song: {song_name}")
        speak(f"Sorry, I couldn't find {song_name} on YouTube.")

def search_wikipedia(query):
    wikipedia_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query)}"
    webbrowser.open(wikipedia_url)
    speak(f"Opening Wikipedia page for {query}")

def search_folder(folder_name):
    matches = []

    # Get a list of drives (including C:, D:, E:)
    drives = [drive for drive in ['C', 'D', 'E'] if os.path.exists(f"{drive}:\\")]

    for drive in drives:
        # Walk through the directory in each drive
        for root, dirs, files in os.walk(f"{drive}:\\"):
            if folder_name.lower() in dirs:
                matches.append(root)  # Store the root path, which is the folder's full directory path

    if not matches:
        speak(f"No folders found with the name {folder_name}.")
    else:
        speak(f"Found {len(matches)} folder(s) named {folder_name}. Here are the options:")

        # List both the full directory path and folder name
        for idx, folder in enumerate(matches, 1):
            folder_name_only = folder.split(os.sep)[-1]  # Extract just the folder name
            print(f"{idx}) Drive: {folder.split(os.sep)[0]} - Folder: {folder_name_only}")
            speak(f"{idx}) Drive: {folder.split(os.sep)[0]} - Folder: {folder_name_only}")

        speak("Do you want to open any of these? Please type the number of the folder you want to open.")

        # Give the user a chance to type the number instead of voice input
        folder_choice = input("Enter the folder number to open or type 'exit' to cancel: ")

        if folder_choice.lower() == 'exit':
            speak("Cancelled. No folder will be opened.")
        else:
            try:
                # If the user provides a valid number, open the corresponding folder
                choice = int(folder_choice.strip())
                if 1 <= choice <= len(matches):
                    folder_to_open = matches[choice - 1]
                    speak(f"Opening {folder_to_open}.")
                    os.startfile(folder_to_open)
                else:
                    speak("Invalid choice. Please try again.")
            except ValueError:
                speak("Sorry, I didn't understand the choice. Please try again.")

def create_folder(folder_name):
    try:
        os.makedirs(folder_name)
        speak(f"Folder '{folder_name}' has been created.")
    except FileExistsError:
        speak(f"Folder '{folder_name}' already exists.")
    except Exception as e:
        speak(f"An error occurred: {str(e)}")

def search_internet(query):
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    print(f"Searching internet for: {query}")
    webbrowser.open(url)
    speak(f"Searching the internet for {query}")

def nura():
    greet_boss()
    conversation = [
        {"role": "system", "content": "You are Neura, a helpful AI assistant."}
    ]

    active = False

    while True:
        if not active:
            print("Waiting for wake-up command...")
            user_input = listen()
            if "wake up" in user_input:
                speak("I am awake now. How can I assist you?")
                active = True

        else:
            user_input = listen()

            if "exit" in user_input or "quit" in user_input:
                speak("Goodbye!")
                break

            elif " emergency , emergency,send sos" in user_input:
                speak("Sending emergency SOS message.")
                send_sos_message()

            elif "distance" in user_input:
                distance = get_distance()
                if distance is not None:
                    speak(f"The current distance is {distance} centimeters.")
                    print(f"The current distance is {distance} centimeters")
                else:
                    speak("Sorry, I couldn't fetch the distance at the moment.")    

            elif user_input.startswith("open"):
                website_name = user_input.replace("open", "").strip()
                open_website(website_name)

            elif user_input.startswith("play"):
                song_name = user_input.replace("play", "").strip()
                play_song(song_name)

            elif "search folder" in user_input:
                folder_name = user_input.replace("search folder", "").strip()
                search_folder(folder_name)

            elif "create folder" in user_input:
                folder_name = user_input.replace("create folder", "").strip()
                create_folder(folder_name)

            elif "search internet" in user_input:
                query = user_input.replace("search internet", "").strip()
                search_internet(query)

            elif user_input.startswith("launch"):
                app_name = user_input.replace("launch", "").strip()
                launch_application(app_name)     
                
            elif "search wikipedia" in user_input:
                query = user_input.replace("search wikipedia", "").strip()
                result = search_wikipedia(query)
                print(f"Wikipedia result: {result}")
                speak(result)


            else:
                conversation.append({"role": "user", "content": user_input})
                response = ask_neura(conversation)
                print(f"Neura: {response}")
                speak(response)
                conversation.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    nura()

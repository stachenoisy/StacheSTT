import subprocess
import time
import os
from wit import Wit
import random
import json
from typing import Annotated
from fastapi import FastAPI, Request, HTTPException, requests, File, UploadFile, Form, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import logging
import threading
import ngrok
import base64
from mutagen.mp3 import MP3
logging.basicConfig(filename='WebServer.log', filemode='w', level=logging.DEBUG)

DomainName="xxx-xxx.ngrok-free.app"
ngrokToken="xxx-xxx-xxx"

ngrok.set_auth_token(ngrokToken)
listener = ngrok.forward(8000, domain=DomainName)

print("Ingress established at https://trusty-sunfish-firmly.ngrok-free.app")

# System
platform = "Linux"

# Wit.ai API Keys (Multiple can be used in order to avoid rate-limit issues.)
api_keys = [
	"test_fill",
]

wit_api = {}
resp = {}

for api_key in api_keys:
	# Create multiple instances of Wit for every API Application Key.
	wit_api[api_key] = Wit(api_key)

# Windows
if platform == "Windows":
	try:
		if not os.path.exists('C:\\SpeechRecognition'):
			os.mkdir('C:\\SpeechRecognition')
			os.mkdir('C:\\SpeechRecognition\\Cache')
			#os.chdir('C:\\SpeechRecognition')
			logging.debug("Creating Environment for the first time!")
			print("Creating Environment for the first time!")
		else:    
			#os.chdir('C:\\SpeechRecognition')
			logging.debug("Environment already exists.")
			print("Environment already exists.")
	except:
		pass

# Linux
if platform == "Linux":
	try:
		if not os.path.exists('/SpeechRecognition'):
			os.mkdir('/SpeechRecognition')
			os.mkdir('/SpeechRecognition/Cache')
			#os.chdir('/SpeechRecognition')
		else:    
			#os.chdir('/SpeechRecognition')
	except Exception as e:
		print(e)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.route('/')
def index(request: Request):
	raise HTTPException(status_code=500)

class FormData(BaseModel):
    __root__: List[str] = []

@app.post('/speech')
async def process(request: Request, Form: str = Body(...), voicesound: UploadFile = File(...)):
	start_execution = time.time()

	LocalApiKeys = json.loads(Form)["ApiKeys"] if json.loads(Form)["ApiKeys"] else []

	# Request Processing
	data_length = str(round(float(int(request.headers['content-length']) / 1024),2))
	random_hash = random.randint(10000000000,99999999999)

	# Don't allow big requests
	if float(data_length) > 1000:
		print('The incoming speech request has exceeded the 1000KB limit established by the Developer, Size: ' + str(data_length) + "KB")
		return

	print("[" + str(random_hash) + "] Speech request received from " + request.client.host + " | " + " Size of incoming data: " + data_length + "KB.")
	logging.info("[" + str(random_hash) + "] Speech request received from " + request.client.host + " | " + " Size of incoming data: " + data_length + "KB.")

	if LocalApiKeys == None or LocalApiKeys == "" or len(LocalApiKeys) == 0:
		print("[" + str(random_hash) + "] Invalid request received from " + request.client.host)
		raise HTTPException(status_code=403, detail="Invalid request received. Code: 23x546")
		return "Invalid request received. Code: 23x546"

	logging.debug("[" + str(random_hash) + "] .webm obtained from the Body request.")

	# File Writting
	with open("SpeechRecognition/Cache/" + str(random_hash) + ".webm", "wb") as file:
		content = await voicesound.read()  # async read
		file.write(content)
		file.close()
    
	logging.debug("[" + str(random_hash) + "] .webm written to file " + str(random_hash) + ".webm")

	# File Conversion
	logging.debug("[" + str(random_hash) + "] Starting conversion .webm to .mp3")
	start_time = time.time()

	# Windows
	if platform == "Windows":
		file_conversion = subprocess.Popen(["ffmpeg","-i","C:/SpeechRecognition/Cache/" + str(random_hash) + ".webm","-af","silenceremove=stop_periods=-1:stop_duration=0.02:stop_threshold=-53dB","-vn","-ac","1","-b:a","64k","C:/SpeechRecognition/Cache/" + str(random_hash) + ".mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		file_conversion.wait()

	# Linux
	if platform == "Linux":
		convert = subprocess.Popen(["ffmpeg","-i","SpeechRecognition/Cache/" + str(random_hash) + ".webm","-af","silenceremove=stop_periods=-1:stop_duration=0.02:stop_threshold=-53dB","-vn","-ac","1","-b:a","64k","SpeechRecognition/Cache/" + str(random_hash) + ".mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		convert.wait() 

	logging.debug("[" + str(random_hash) + "] Conversion finished, time " + str(round(float((time.time() - start_time) * 1000),2)) + " msec")
	
	# File Open
	with open("SpeechRecognition/Cache/" + str(random_hash) + ".mp3", "rb") as file:
		audio_read = file.read()
		file.close()

	# Audio Length
	length = 0
	try:
		audio = MP3("SpeechRecognition/Cache/" + str(random_hash) + ".mp3")
		length = audio.info.length
	except:
		print("Error reading Audio")

	start_req = time.time()
	random_api_key = random.choice(LocalApiKeys)
	# Req to Wit.Ai
	try:
		resp[random_hash] = wit_api[random_api_key].speech(audio_read, {'Content-Type': 'audio/mpeg3'})
		logging.debug("[" + str(random_hash) + "] .mp3 sent to Wit.Ai | Request to Wit.Ai completed in " + str(round(float((time.time() - start_req) * 1000),2)) + " msec | Audio Length: " + str(round(float(length),2)) + "s")
		print("[" + str(random_hash) + "] .mp3 sent to Wit.Ai | Request to Wit.Ai completed in " + str(round(float((time.time() - start_req) * 1000),2)) + " msec | Audio Length: " + str(round(float(length),2)) + "s")
		print("[" + str(random_hash) + "] Recognized text ", resp[random_hash])
	except Exception as e:
		logging.debug(e)
		logging.info("[" + str(random_hash) + "] Unable to make request, manual check required.")

	# Clean-up
	def RemoveEnvironment(random_hash):
		try:
			os.remove("SpeechRecognition/Cache/" + str(random_hash) + ".webm")
			os.remove("SpeechRecognition/Cache/" + str(random_hash) + ".mp3")
			logging.debug("[" + str(random_hash) + "] Cleaned up environment.")
		except:
			logging.debug("[" + str(random_hash) + "] Unable to clean environment.")

	# On a Thread, faster execution
	threading.Thread(target=RemoveEnvironment, args=[random_hash]).start()

	print("[" + str(random_hash) + "] Speech request completed for " + request.client.host)
	logging.info("[" + str(random_hash) + "] Speech request completed for " + request.client.host)

	# # Conversion Time
	logging.info("[" + str(random_hash) + "] Request completed in " + str(round(float((time.time() - start_execution) * 1000),2)) + " msec")
	print("[" + str(random_hash) + "] Answer from Wit.Ai API: " + resp[random_hash]['text'])
	return resp[random_hash]['text']

from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
from gtts import gTTS
import os
import time
import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)


api_key = 'AIzaSyCqbNXQt10cd3Mg4u2U35k0lcqVEse6ow8'
API_URLText = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}'
headers = {'Content-Type': 'application/json'}
instructions = """
Je bent vanaf nu een studiekeuzeadviseur die middelbare scholieren helpt bij het vinden van de opleiding die het beste bij hen past. Je ondersteunt hen door inzicht te geven in hun interesses, capaciteiten en voorkeuren, en geeft advies over mbo-, hbo- en wo-opleidingen. Je volgt de onderstaande werkwijze om scholieren te begeleiden:



Begin met een kennismakingsgesprek: Vraag naar de scholier zijn of haar huidige situatie en persoonlijke voorkeuren, en vraag ook naar het huidige educatieniveau om te begrijpen welke opleidingen passend kunnen zijn. Stel open vragen zoals:

'Wat is je huidige educatieniveau?'

'Wat vind je leuk om te doen in je vrije tijd?'

'Wat vakken vond je het afgelopen jaar het leukste op school?'

'Wat zou je willen bereiken in de toekomst?'

Begrijp de sterke punten van de scholier: Vraag naar de scholier zijn of haar vaardigheden en capaciteiten, bijvoorbeeld:

'Wat denk je dat je sterke punten zijn op school?'

'Welke vakken vallen je het gemakkelijkst en het moeilijkst?'

'Heb je eerder aan projecten gewerkt waar je trots op bent?'

Verken de persoonlijke voorkeuren van de scholier: Probeer inzicht te krijgen in de voorkeuren van de scholier voor studieomgevingen en werkvelden:

'Werk je liever met je handen of achter een computer?'

'Heb je meer interesse in theorie of praktijk?'

'Wil je werken in een team of meer zelfstandig?'

Verken toekomstverwachtingen: Vraag naar de lange-termijn verwachtingen en doelen, zoals:

'Heb je al een idee van wat voor werk je later zou willen doen?'

'Ben je bereid om eventueel naar een andere stad te verhuizen voor je studie?'

Adviseer over passende opleidingen: Op basis van de antwoorden geef je gericht advies over mogelijke mbo-, hbo- of wo-opleidingen. Stel vervolgvragen om verder af te stemmen:

'Op basis van je interesses in techniek en het werken met je handen, zou een technische opleiding goed kunnen passen. Wat denk je van een mbo-opleiding in de richting van werktuigbouwkunde?'

'Omdat je aangeeft geïnteresseerd te zijn in marketing en creatief denken, zou een hbo-opleiding in communicatie of marketing goed bij je kunnen passen.'

Ondersteun bij de praktische overwegingen: Bespreek praktische zaken zoals locatie, duur van de opleiding, en benodigde toelatingseisen. Vraag bijvoorbeeld:

'Heb je voorkeur voor een studie dichtbij huis, of zou je naar een andere stad willen?'

'Ben je op de hoogte van de toelatingseisen voor de opleidingen die je overweegt?'

Bied empathische en opbouwende feedback: Wanneer de scholier twijfels heeft, bied dan geruststelling en help hen de keuze te verhelderen door twijfels bespreekbaar te maken:

'Het is heel normaal om je onzeker te voelen over je keuze, maar dit proces helpt je om je eigen interesses en sterke punten beter te begrijpen.'

'Als je het nog lastig vindt om een keuze te maken, kun je overwegen om een meeloopdag te volgen bij een studie of om met een student in dat vakgebied te praten.'

Stel vervolgstappen voor: Moedig de scholier aan om actie te ondernemen, zoals het onderzoeken van specifieke opleidingen of het volgen van open dagen. Stel hierbij een concrete vervolgvraag:

'Wat zou je als volgende stap willen doen om meer te weten te komen over deze opleiding?'

'Zou je graag wat meer informatie willen ontvangen over de toelatingseisen of open dagen?

"""



def send_message(message, instructions=None):
    """Sends a message to Gemini and returns the response.
       Includes instructions if provided.
    """

    data = {
        "contents": [{"parts": [{"text": message}]}]
    }
    if instructions:
        data["contents"][0]["parts"].insert(0, {"text": instructions})

    response = requests.post(API_URLText, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")



def query_flowise(payload):
    response = requests.post(API_URLText, json=payload)
    return response.json()


def text_to_speech(text, language='nl'):
    
    timestamp = int(time.time())  
    audio_file = f"static/response_{timestamp}.mp3"  
    
    
    if not os.path.exists("static"):
        os.makedirs("static")

    
    tts = gTTS(text=text, lang=language)
    tts.save(audio_file)
    
    return audio_file

# To keep track of the chat
chat_history = []

@app.route('/')
def home():
    return render_template('chat.html', chat_history=chat_history)

@app.route('/ask', methods=['POST'])
def ask():
    # Get the question from the form
    question = request.form['question']
    
    # Get the response from Flowise
    output = send_message(question, instructions)
    text_response = output["parts"][0]["text"]
    
    # Add question and answer to chat history
    chat_history.append({'question': question, 'response': text_response})
    
    # Convert the response to speech and get the path to the audio file
    audio_file = text_to_speech(text_response)
    
    # Return the updated chat history and the audio file path to the template
    return render_template('chat.html', chat_history=chat_history, audio_file=f'/{audio_file}')

# Serve the audio file from the static directory
@app.route('/static/<filename>')
def send_audio(filename):
    return send_from_directory('static', filename)

@app.route('/generate', methods=['POST'])
def generate_image():
    image_prompt = request.form['image_prompt']


    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev" 
    headers = {
        "Authorization": "Bearer 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"
    }
    payload = image_prompt
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        image_data = response.content
        
        image = Image.open(BytesIO(image_data))
        
        image.show()
        image_path = "img/generated_image.png"
        image.save(image_path)
        return jsonify({"image_url": f"/img/generated_image.png"})

    else:
        jsonify({"error": "Failed to generate image"}), 400

@app.route('/img/<filename>')
def serve_image(filename):
    return send_from_directory('img', filename)
    
if __name__ == '__main__':
    app.run(debug=True)




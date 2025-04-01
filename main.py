import json
import websocket
import pyaudio
import base64
import struct
import threading
import time
import numpy as np

CHUNK = 1024
FORMAT = pyaudio.paInt16  # 16비트 PCM
CHANNELS = 1  # 모노
RATE = 24000

connected = False
output = True

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

output_stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       output=True,
                       frames_per_buffer=CHUNK)

M = 32  # 필터 탭 수 (필터 길이)
step = 0.1

reference_signal = None

OPENAI_API_KEY = ''
with open('./key.txt', 'r') as f:
    OPENAI_API_KEY = f.readline()
    f.close()
print(OPENAI_API_KEY)

url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
headers = [
    "Authorization: Bearer " + OPENAI_API_KEY,
    "OpenAI-Beta: realtime=v1"
]
def float_to_16bit_pcm(float32_array):
    clipped = [max(-1.0, min(1.0, x)) for x in float32_array]
    pcm16 = b''.join(struct.pack('<h', int(x * 32767)) for x in clipped)
    return pcm16

def base64_encode_audio(float32_array):
    pcm_bytes = float_to_16bit_pcm(float32_array)
    encoded = base64.b64encode(pcm_bytes).decode('ascii')
    return encoded

def on_open(ws):
    global connected
    print("Connected to server.")
    prompt = """In this session, all inputs must be recognized as Korean and responses must be made in Korean. Any other language must be ignored."""
    pr = {
        "type": "session.update",
        "session": {
            "modalities": ["text", "audio"],
            "instructions": "You are a helpful assistant. and only speak korean",
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "temperature": 0.8
        }
    }

    ws.send(json.dumps(pr))
    time.sleep(1)
    event = {
        "type": "response.create",
        "response": {
            # Setting to "none" indicates the response is out of band,
            # and will not be added to the default conversation
            "conversation": "none",

            # Set metadata to help identify responses sent back from the model
            "metadata": { "topic": "classification" },

            # Set any other available response fields
            "modalities": [ "audio", 'text' ],
            "instructions": "say hello",
        },
    }

    ws.send(json.dumps(event))
    connected = True

def on_message(ws, message):
    global reference_signal, output
    data = json.loads(message)
    print(f"{data['type']} Received event:", json.dumps(data, indent=2))

    if data['type'] == "response.done":
        output = True
        print(data['response']['output'][0])

    if data['type'] == "response.audio.delta":
        try:
            output = False
            print('!(*@#&(!@#&*()))')
            d = base64.b64decode(data['delta'])
            reference_signal = d
            output_stream.write(d)
        except Exception as e: print('ERROR!!!\t',e)
        
    if data['type'] == 'response.audio_transcript.done':
        print(data['transcript'])

ws = websocket.WebSocketApp(
    url,
    header=headers,
    on_open=on_open,
    on_message=on_message,
)

def remove_echo(input_signal, echo_signal, filter_length=1024, mu=0.1):
    # 적응 필터 초기화
    filter_weights = np.zeros(filter_length)
    output_signal = np.zeros_like(input_signal)

    for i in range(len(input_signal)):
        # 입력 신호의 최근 샘플 가져오기
        input_buffer = input_signal[max(0, i - filter_length + 1):i + 1]
        input_buffer = np.pad(input_buffer, (max(0, filter_length - len(input_buffer)), 0))

        # 에코 추정
        estimated_echo = np.dot(filter_weights, input_buffer)

        # 에러 계산
        error = echo_signal[i] - estimated_echo

        # 필터 가중치 업데이트
        filter_weights += 2 * mu * error * input_buffer

        # 출력 신호 계산
        output_signal[i] = input_signal[i] - estimated_echo

    return output_signal

def run():
    global connected, reference_signal, output
    while not connected: pass
    print('Start SEND MIC')
    while True:
        try:
            data = stream.read(CHUNK)
            event = {
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(data).decode('ascii')#base64_encode_audio(stream.read(CHUNK))
            }
            if output: ws.send(json.dumps(event))
        except Exception as e: print("ERROR!",e)
th = threading.Thread(target=run, daemon=True)
th.start()

ws.run_forever()

th.join()

stream.stop_stream()
stream.close()
output_stream.stop_stream()
output_stream.close()
p.terminate()
if ws:
    ws.close()
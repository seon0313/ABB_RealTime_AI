from RealTime import RealTime

OPENAI_API_KEY = ''
with open('./key.txt', 'r') as f:
    OPENAI_API_KEY = f.readline()
    f.close()
print(OPENAI_API_KEY)
r = RealTime(OPENAI_API_KEY)

r.connect()

while True:
    pass#print('wait')

'''error Received event: {
  "type": "error",
  "event_id": "event_BI4PeaRiLrbSZzzQQ75AG",
  "error": {
    "type": "invalid_request_error",
    "code": "invalid_api_key",
    "message": "Incorrect API key provided: ''. You can find your API key at https://platform.openai.com/account/api-keys.",
    "param": null,
    "event_id": null
  }
}'''
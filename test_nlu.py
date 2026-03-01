# test_nlu.py — run once to verify nothing downstream breaks
# This is a independent file, and is not linked to any main files.
# Use Case: To test and check proper functionaing of nlu_engine.

from nlu_engine import parse_intent

cases = [
    "what's the weather in Bhubaneswar",
    "take me to AIIMS",
    "play Kesariya",
    "call mom",
    "what causes traffic jams",
    "is it raining",           # weather, no location
    "play something",          # music, no song
]

for text in cases:
    result = parse_intent(text)
    print(f"\n'{text}'")
    print(f"  intent     : {result['intent']}")
    print(f"  entities   : {result['entities']}")
    print(f"  confidence : {result['confidence']}")
    print(f"  assumptions: {result['assumptions']}")

'''
Expected outputs that would indicate everything is working:

'what's the weather in Bhubaneswar'
  intent     : GET_WEATHER
  entities   : {'location': 'Bhubaneswar'}
  confidence : 0.95
  assumptions: []

'play something'
  intent     : GET_MUSIC
  entities   : {}
  confidence : 0.7
  assumptions: ['missing_song']

'what causes traffic jams'
  intent     : UNKNOWN
  entities   : {}
  confidence : 0.3
  assumptions: []
  
'''
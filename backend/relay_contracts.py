"""Data allowed to leave the helper. No Apple identity, addresses or trust records."""
import math
from backend.contracts import Coordinates,Frame,TripSummary

def checked(model,value):
    if not isinstance(value,dict):return None
    try:return model.model_validate(value).model_dump()
    except ValueError:return None

def text(value,limit=160):return value[:limit] if isinstance(value,str) else None

def number(value,maximum):
    return value if type(value) in (int,float) and math.isfinite(value) and 0<=value<=maximum else 0

def choice(value,allowed,fallback):return value if isinstance(value,str) and value in allowed else fallback

def safe_status(status):
    if not isinstance(status,dict):status={}
    phone=status.get('device') if isinstance(status.get('device'),dict) else {}
    raw=status.get('journey') if isinstance(status.get('journey'),dict) else {}
    journey={key:number(raw.get(key),bound) for key,bound in [('index',30000),('totalFrames',30000),('elapsed',28800),('duration',28800),('phaseRemaining',28800),('totalDistance',2000000),('acknowledgedSamples',30000)]}
    journey.update(state=text(raw.get('state'),30) or 'idle',frame=checked(Frame,raw.get('frame')),trip=checked(TripSummary,raw.get('trip')),phase=choice(raw.get('phase'),{'outbound','stay','return','complete'},'outbound'),playbackRate=raw.get('playbackRate') if type(raw.get('playbackRate')) in (int,float) and .25<=raw['playbackRate']<=4 else 1,error='The home helper paused this journey. Check its local device connection.' if raw.get('error') else None)
    return {'state':text(status.get('state'),30) or 'unknown','connection':choice(status.get('connection'),{'connected','connecting','disconnected'},'disconnected'),'simulation':text(status.get('simulation'),40) or 'unknown','helperVersion':text(status.get('helperVersion'),20),'lastAcceptedCoordinates':checked(Coordinates,status.get('lastAcceptedCoordinates')),'holdRefreshes':number(status.get('holdRefreshes'),1000000),'acknowledgedLocationWrites':number(status.get('acknowledgedLocationWrites'),1000000),'device':{'name':text(phone.get('name'),80) or 'iPhone','ios':text(phone.get('ios'),20) or 'Unknown','transport':choice(phone.get('transport'),{'USB','Wi-Fi'},'Unknown')} if phone else None,'journey':journey}

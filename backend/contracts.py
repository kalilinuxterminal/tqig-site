from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictBody(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)

class Coordinates(StrictBody):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)

class ConnectBody(StrictBody):
    id: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9-]+$')
    transport: Literal['usb','wifi'] = 'usb'

class Frame(Coordinates):
    t: float = Field(ge=0, le=28800)
    distance: float = Field(ge=0, le=2000000)
    speed: float = Field(ge=0, le=80)
    event: Literal['move','signal','intersection','arrival','stay'] = 'move'
    phase: Literal['outbound','stay','return','complete'] = 'outbound'

class TripSummary(StrictBody):
    outboundDuration: float = Field(ge=0, le=28800)
    stayDuration: float = Field(ge=0, le=14400)
    returnDuration: float = Field(ge=0, le=28800)
    outboundDistance: float = Field(ge=0, le=2000000)
    returnDistance: float = Field(ge=0, le=2000000)
    returnToStart: bool
    travelMode: Literal['walking','driving']

class RouteBody(StrictBody):
    frames: list[Frame] = Field(min_length=2, max_length=30000)
    name: str = Field(max_length=100, default='Journey')
    playbackRate: float = Field(ge=0.25, le=4, default=1.0)
    trip: TripSummary | None = None

class PortableObservation(StrictBody):
    result: Literal['persists','restored','unknown']
    observedSeconds: int = Field(ge=30, le=86400)
    app: Literal['Apple Maps','Snapchat','Life360','Find My']

class WifiSetup(StrictBody):
    confirm: Literal[True]

class RemoteLink(StrictBody):
    code: str = Field(min_length=20,max_length=100)
    confirm: Literal[True]

class WifiAddress(StrictBody):
    address: str = Field(min_length=3,max_length=60)

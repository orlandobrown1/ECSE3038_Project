

from fastapi import FastAPI, Request
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
import re
import requests
import datetime
import pydantic
import motor.motor_asyncio
import pytz

app = FastAPI()


origins = [
    "https://simple-smart-hub-client.netlify.app",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



client = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://orlandobrown:collegeboy@cluster0.qugvaa8.mongodb.net/")
db = client.project
sensor_readings = db["sensor_readings"]
values = db ["values"]

pydantic.json.ENCODERS_BY_TYPE[ObjectId]=str



geolocator = Nominatim(user_agent="MyApp")
location = geolocator.geocode("Hyderabad")


def get_sunset():
    lat =  location.latitude
    lng = location.longitude

    endpoint = f'https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}'

    api_response = requests.get(endpoint)
    api_data = api_response.json()

    sunset_time = datetime.datetime.strptime(api_data['results']['sunset'], '%I:%M:%S %p').time()
    
    return datetime.datetime.strptime(str(sunset_time),"%H:%M:%S")





regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

def parse_time(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)



@app.get("/")
async def home():
    return {"message": "ECSE3038 - Project"}


@app.get('/graph')
async def graph(request: Request):
    size = int(request.query_params.get('size'))

    graph_plot = await values.find().sort('_id', -1).limit(size).to_list(size)

    graph_data = []

    for stuff in graph_plot:
        temperature = stuff.get("temperature")
        presence = stuff.get("presence")
        current_time = stuff.get("current_time")

        graph_data.append({
            "temperature": temperature,
            "presence": presence,
            "datetime": current_time
        })

    return graph_data


@app.put('/settings')
async def get_sensor_readings(request: Request):
    setting = await request.json()

    user_temp = setting["user_temp"]
    user_light = setting["user_light"]
    light_time_off = setting["light_duration"]
    

    if user_light == "sunset":
        light_adder = get_sunset()
    else:
        light_adder = datetime.datetime.strptime(user_light, "%H:%M:%S")
    
    new_user_light = light_adder + parse_time(light_time_off)

    final_setting = {
        "user_temp": user_temp,
        "user_light": str(light_adder.time()),
        "light_time_off": str(new_user_light.time())
        }

    addition = await sensor_readings.find().sort('_id', -1).limit(1).to_list(1)

    if addition:
        await sensor_readings.update_one({"_id": addition[0]["_id"]}, {"$set": final_setting})
        new_addition = await sensor_readings.find_one({"_id": addition[0]["_id"]})
    else:
        new = await sensor_readings.insert_one(final_setting)
        new_addition = await sensor_readings.find_one({"_id": new.inserted_id})
    return new_addition



@app.post("/values")
async def readings(request: Request): 
    value = await request.json()

    setting = await sensor_readings.find().sort('_id', -1).limit(1).to_list(1)
    
    if setting:
      temperature = setting[0]["user_temp"]   
      user_light = datetime.datetime.strptime(setting[0]["user_light"], "%H:%M:%S")
      light_time_off = datetime.datetime.strptime(setting[0]["light_time_off"], "%H:%M:%S")
    else:
      temperature = 28
      user_light = datetime.datetime.strptime("18:00:00", "%H:%M:%S")
      light_time_off = datetime.datetime.strptime("20:00:00", "%H:%M:%S")

    now_time = datetime.datetime.now(pytz.timezone('Jamaica')).time()
    current_time = datetime.datetime.strptime(str(now_time),"%H:%M:%S.%f")


    value["light"] = ((current_time < user_light) and (current_time < light_time_off ) & (value["presence"] == 1 ))
    value["fan"] = ((float(value["temperature"]) >= temperature) & (value["presence"]==1))
    value["current_time"]= str(datetime.datetime.now())

    new_settings = await values.insert_one(value)
    new_addition = await values.find_one({"_id":new_settings.inserted_id}) 
    return new_addition




@app.get("/state")
async def get_state():
    last_entry = await values.find().sort('_id', -1).limit(1).to_list(1)

    if not last_entry:
        return {
            "presence": False,
            "fan": False,
            "light": False,
            "current_time": datetime.datetime.now()
        }

    return last_entry

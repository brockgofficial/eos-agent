import os, platform, time, requests, json #temp
from modules.sockets.agent_core_setup import retreive_config_details, send_agent_details, get_agent_details
from modules.metrics.client_metrics import start_agent as enable_data_collection
from modules.metrics.client_metrics import get_json


#Define any constant expressions
DELAY_TIME = 20
BASEDIR = os.path.abspath(os.path.dirname(__file__))
if platform.system() == "Windows":
  CONFIG_PATH = BASEDIR + "\\agent-config.cfg"
else:
  CONFIG_PATH = BASEDIR + "/agent-config.cfg"

#Import the config
agent_config_details = retreive_config_details(CONFIG_PATH)

#Server API address
api_endpoint = "http://"
if agent_config_details["server_https_enabled"] == "true":
  api_endpoint = "https://"
api_endpoint += str(agent_config_details["server_ip"])+":"+str(agent_config_details["server_port"])

#Start up agent, with data collection, socket listeners and loop
#Sending machine details untill successful
while True:
  result = send_agent_details(api_endpoint+"/test/senddetails", get_agent_details())
  if result:
    break
  time.sleep(DELAY_TIME)

#Start the data collection unit
#combine metric collector with metric sender
#possibly collating info and sending every 5 mins
enable_data_collection()



def collect_data():
  timeout = 300   # 5 mins
  timeout_start = time.time() # current time
  
  metrics = [] #LIST for data collection

  while time.time() < timeout_start + timeout: 
      data = json.loads(get_json())   #JSON Object
      metrics.append(data)  # passing the data into the list.
      time.sleep(10)

  print("5 mins are up. posting data now.")

  requests.post("http://localhost:5000/test/addmetrics", data=metrics) # not sure about this one
  return metrics
 
#def commands():
    # listen for commands via socket? or api

    



      
#Start collection thread loop

#Setup socket listeners (start listening loops)
# - for handling real time data gathering and commands

#Infinite while loop to keep the program alive, currently
# - grabs data periodically and displays it


while True:
 time.sleep(DELAY_TIME/2)
 metrics = json.loads(get_json())
 print(str(metrics["collection_time"]) + " - " + str(metrics["machine_name"]) + " - " + str(metrics["system_metrics"][0]["cpu"]))
  
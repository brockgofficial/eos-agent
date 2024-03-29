#
# Handles all the core functionalities for the agent
# such as data retrieval and sending, and metric collecting and sending
#

#Import third party libraries
import socket, threading, sys, platform, ipaddress, requests, time, json
import ifcfg
from datetime import datetime
from getmac import get_mac_address

#Import custom modules
from .logging_setup import agent_logger
from ..metrics.client_metrics import get_json
from ..metrics.client_metrics import start_agent as enable_data_collection

#Function: Generate and start a new thread
#Params:
#   - target_function: the function the thread will run
#   - target_args:     the corresponding function arguments
#Returned:
#   - None
def create_new_thread(target_function, target_args = ()):
  t = threading.Thread(target=target_function, args=target_args)
  t.daemon = True
  t.start()

#Function: Get the agents machine details
#Params: - None
#Returned:
#   - Dict/JSON object of the required machine details
def get_agent_details(socket_address, main_port, secondary_port):
  return {
    "os_type": platform.system(),
    "os_details": platform.platform(),
    "os_release": platform.release(),
    "os_version": platform.version(),
    "processor_type": platform.processor(),
    "host_name": socket.gethostname(),
    "ip_addr_v4": int(ipaddress.IPv4Address(socket_address)), #socket.gethostbyname(socket.gethostname())
    "port_numbers": [str(main_port),str(secondary_port)], 
    "mac_addr": get_mac_address()
  }

#Function: Send the collected machine details to the API
#Params:
#   - server_address_route: API route to send the message e.g. http://localhost:5000/senddetails
#   - agent_details: the collected agent details
#Returned:
#   - True (if successful) or False (if unsuccessful)
def send_agent_details(server_address_route, agent_details, retry_timer):
  agent_logger.info("Attempting to send the agent details to {}.".format(server_address_route))
  try:
    #Send the details to the API
    api_result = requests.post(server_address_route, json=agent_details)
    if api_result.status_code == 200 and api_result.text == "Success":
      #Successful result
      agent_logger.info("Agent details have successfully sent to {}.".format(server_address_route))
      return True
    elif api_result.status_code == 200:
      #Status code error
      agent_logger.error("A connection to {} was established; however, an error occurred, re-trying in {} minutes.".format(server_address_route, round(retry_timer/60, 2)))
      agent_logger.error(str(api_result.text))
      return False
    else:
      #Issue with the data on the backend
      agent_logger.error("Failure occurred: ({}) {}, retrying in {} minutes.".format(str(api_result.status_code), str(api_result.reason), round(retry_timer/60, 2)))
      return False
  except Exception as err:
    #Cannot connect to the server
    agent_logger.error("Failed to connect to {}, re-trying in {} minutes.".format(server_address_route, round(retry_timer/60, 2)))
    return False

#Function: Send the machine metrics to the API
#Params:
#   - api_route: API route to send the message e.g. http://localhost:5000/metrics/commitmetrics
#   - collection_interval: interval to collect data from the polling threads
#   - post_interval: interval until data can be sent
#Returned:
#   - None
def data_processing(api_route, collection_interval, post_interval):
  timeout = post_interval #Gets the timeout value when function is ran
  while True:
    timeout_start = datetime.timestamp(datetime.now()) #Starts the inital timeout value
    metrics = []

    while datetime.timestamp(datetime.now()) < timeout_start + timeout: #Runs till the assigned time is up
      data = json.loads(get_json())  #Gets the JSON Data
      metrics.append(data) #Adds it to the list
      time.sleep(collection_interval) #Sleeps for assigned time
    
    agent_logger.info("{} minutes has been reached sending data to {}.".format(round(post_interval/60), api_route)) #Printing the info on logger agent file.
    try:
      requests.post(api_route, json={"content": metrics}) #posting the metrics to the api in a JSON format
    except Exception as err_msg:
      agent_logger.error("Failed to send metrics to the API")

#Function: Thread the data collection and sending
#Params:
#   - api_route: API route to send the message e.g. http://localhost:5000/metrics/commitmetrics
#   - collection_interval: interval to collect data from the polling threads
#   - post_interval: interval until data can be sent
#Returned:
#   - None
def data_collection(api_route, coll_interval, post_interval):
  #Start the data collection polls
  enable_data_collection()
  agent_logger.info("Data collection threads started")
  time.sleep(10)
  create_new_thread(data_processing, [api_route, coll_interval, post_interval])
  agent_logger.info("Data processing and sending thread started.")
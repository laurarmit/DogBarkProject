#
# greengrassDogBarkSensor.py
#
# This is a Python AWS lambda function that is designed to be deployed to a Raspberry Pi,
# via AWS IoT Greengrass v2
#
# The Raspberry Pi has a USB Sound Level Meter that will return the noise level in decibels
# It will sample the noise level and publish it to AWS IoT via MQTT message topic dogbark/decibels/#
#
# It is based on the AWS example program "greengrassHelloWorld.py" at:
#   https://github.com/aws/aws-greengrass-core-sdk-python
#
# Plus code for reading sound level measurements from the USB device at:
#   http://www.swblabs.com/article/pi-soundmeter
#
# The function is long-lived.  It will sleep for 5 seconds, publish a reading from the
# sound meter, then repeat.
# 
# As per the original "greengrassHelloWorld.py" sample code, the handler function will NOT
# be invoked because it runs in an infinite loop.

import uuid
import re
import logging
import sys
import json
import datetime
import usb.core
from threading import Timer

import greengrasssdk

# Set static parameters for the lambda function
frequency   = 5
mac_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))

# Setup logging to stdout
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Creating a greengrass core sdk client
client = greengrasssdk.client("iot-data")

# When deployed to a Greengrass core, this code will be executed immediately
# as a long-lived lambda function.  The code will enter the infinite while
# loop below.
# If you execute a 'test' on the Lambda Console, this test will fail by
# hitting the execution timeout of three seconds.  This is expected as
# this function never returns a result.


def greengrass_dog_bark_sensor_run():
    dB = ''

    try:
        # Take reading
        dev = usb.core.find(idVendor=0x16c0, idProduct=0x5dc)

        if dev is None:
            logger.error("Failed to find USB device")
        else:
            ret = dev.ctrl_transfer(0xC0, 4, 0, 0, 200)
            dB = str((ret[0]+((ret[1]&3)*256))*0.1+30)

            timestamp = str(datetime.datetime.now())

            payload = {
                "device_id": mac_address,
                "timestamp": timestamp,
                "decibels": dB,
            }

            # Publish to IoT Core
            client.publish(
                topic='dogbark/reading/{mac_address}'.format(mac_address=mac_address),
                queueFullPolicy="AllOrException",
                payload=json.dumps(payload),
            )
    except Exception as e:
        logger.error("Failed to publish message: " + repr(e))

    # Asynchronously schedule this function to be run again in 5 seconds
    Timer(frequency, greengrass_dog_bark_sensor_run).start()


# Start executing the function above
greengrass_dog_bark_sensor_run()


# This is a dummy handler and will not be invoked
# Instead the code above will be executed in an infinite loop for our example
def function_handler(event, context):
    return

# -*- coding: utf-8 -*-

# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in
# compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.

"""Alexa Smart Home Lambda Function Sample Code.

This file demonstrates some key concepts when migrating an existing Smart Home skill Lambda to
v3, including recommendations on how to transfer endpoint/appliance objects, how v2 and vNext
handlers can be used together, and how to validate your v3 responses using the new Validation
Schema.

Note that this example does not deal with user authentication, only uses virtual devices, omits
a lot of implementation and error handling to keep the code simple and focused.
"""

"""
Deployment:

1. Initialize (only once)
In command terminal, execute:
> zappa init

2. Deploy
2.1 Option 1: packaging and upload onto AWS
step 1: setup (only once)
> zappa deploy
step 2: update (each time after code is modified)
> zappa update

2.2 Option 2: only packaging into python.zip, you'll need to upload it manually afterward
> zappa package dev -o python.zip

refer to https://github.com/Miserlou/Zappa
"""

import logging
import time
import json
import uuid

# Imports for v3 validation
from validation import validate_message

# Import Appliances
from appliances import SAMPLE_APPLIANCES
from config import PARTICLE_DEVICE_ID, PARTICLE_NODE_MAIN, PARTICLE_DEFAULT_MODEL

# Import Spark Cloud Lab
from spyrk import SparkCloud

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(request, context):
    """Main Lambda handler.

    Since you can expect both v2 and v3 directives for a period of time during the migration
    and transition of your existing users, this main Lambda handler must be modified to support
    both v2 and v3 requests.
    """

    try:
        logger.info("Directive:")
        logger.info(json.dumps(request, indent=4, sort_keys=True))

        version = get_directive_version(request)

        if version == "3":
            logger.info("Received v3 directive!")
            if request["directive"]["header"]["name"] == "Discover":
                response = handle_discovery_v3(request)
            else:
                response = handle_non_discovery_v3(request)

        else:
            logger.info("Received v2 directive!")
            if request["header"]["namespace"] == "Alexa.ConnectedHome.Discovery":
                response = handle_discovery()
            else:
                response = handle_non_discovery(request)

        logger.info("Response:")
        logger.info(json.dumps(response, indent=4, sort_keys=True))

        if version == "3":
            logger.info("Validate v3 response")
            validate_message(request, response)

        return response
    except ValueError as error:
        logger.error(error)
        raise


# v2 handlers
def handle_discovery():
    header = {
        "namespace": "Alexa.ConnectedHome.Discovery",
        "name": "DiscoverAppliancesResponse",
        "payloadVersion": "2",
        "messageId": get_uuid()
    }
    payload = {
        "discoveredAppliances": SAMPLE_APPLIANCES
    }
    response = {
        "header": header,
        "payload": payload
    }
    return response


def handle_non_discovery(request):
    request_name = request["header"]["name"]
    access_token = request["payload"]["accessToken"]
    particle_device = get_directive_deviceid(request)
    particle_node = get_directive_nodeid(request)
    particle_model = get_directive_model(request)

    spark = SparkCloud(access_token)
    sparkDevice = spark.devices[particle_device]

    if request_name == "TurnOnRequest":
        header = {
            "namespace": "Alexa.ConnectedHome.Control",
            "name": "TurnOnConfirmation",
            "payloadVersion": "2",
            "messageId": get_uuid()
        }
        if sparkDevice.connected:
            # Call cloud function
            if particle_model == "Smart Switch":
                cmd_obj = dict(cmd=8, nd=particle_node, msg=1, ack=1, tag=65, pl="1")
            else:
                cmd_obj = dict(cmd=1, nd=particle_node, state=1)
            cmd_string = json.dumps(cmd_obj)
            sparkDevice.JSONCommand(cmd_string)
    elif request_name == "TurnOffRequest":
        header = {
            "namespace": "Alexa.ConnectedHome.Control",
            "name": "TurnOffConfirmation",
            "payloadVersion": "2",
            "messageId": get_uuid()
        }
        if sparkDevice.connected:
            # Call cloud function
            if particle_model == "Smart Switch":
                cmd_obj = dict(cmd=8, nd=particle_node, msg=1, ack=1, tag=66, pl="1")
            else:
                cmd_obj = dict(cmd=1, nd=particle_node, state=0)
            cmd_string = json.dumps(cmd_obj)
            sparkDevice.JSONCommand(cmd_string)
    elif request_name == "SetPercentageRequest":
        header = {
            "namespace": "Alexa.ConnectedHome.Control",
            "name": "SetPercentageConfirmation",
            "payloadVersion": "2",
            "messageId": get_uuid()
        }
        if sparkDevice.connected:
            # Call cloud function
            brightness = request["payload"]["percentageState"]["value"]
            cmd_obj = dict(cmd=3, nd=particle_node, value=brightness)
            cmd_string = json.dumps(cmd_obj)
            sparkDevice.JSONCommand(cmd_string)

    # other handlers omitted in this example
    payload = {}
    response = {
        "header": header,
        "payload": payload
    }
    return response


# v2 utility functions
def get_appliance_by_appliance_id(appliance_id):
    for appliance in SAMPLE_APPLIANCES:
        if appliance["applianceId"] == appliance_id:
            return appliance
    return None


def get_utc_timestamp(seconds=None):
    return time.strftime("%Y-%m-%dT%H:%M:%S.00Z", time.gmtime(seconds))


def get_uuid():
    return str(uuid.uuid4())


# v3 handlers
def handle_discovery_v3(request):
    endpoints = []
    for appliance in SAMPLE_APPLIANCES:
        endpoints.append(get_endpoint_from_v2_appliance(appliance))

    response = {
        "event": {
            "header": {
                "namespace": "Alexa.Discovery",
                "name": "Discover.Response",
                "payloadVersion": "3",
                "messageId": get_uuid()
            },
            "payload": {
                "endpoints": endpoints
            }
        }
    }
    return response


def handle_non_discovery_v3(request):
    request_namespace = request["directive"]["header"]["namespace"]
    request_name = request["directive"]["header"]["name"]
    access_token = request["directive"]["endpoint"]["scope"]["token"]
    particle_device = get_directive_deviceid(request)
    particle_node = get_directive_nodeid(request)
    particle_model = get_directive_model(request)

    spark = SparkCloud(access_token)
    sparkDevice = spark.devices[particle_device]
    if request_namespace == "Alexa.PowerController":
        if request_name == "TurnOn":
            value = "ON"
        else:
            value = "OFF"

        if sparkDevice.connected:
            # Call cloud function
            if particle_model == "Smart Switch":
                cmd_obj = dict(cmd=8, nd=particle_node, msg=1, ack=1, tag=65 if value == 'ON' else 66, pl="1")
            else:
                cmd_obj = dict(cmd=1, nd=particle_node, state=1 if value == 'ON' else 0)
            cmd_string = json.dumps(cmd_obj)
            sparkDevice.JSONCommand(cmd_string)

        response = {
            "context": {
                "properties": [
                    {
                        "namespace": "Alexa.PowerController",
                        "name": "powerState",
                        "value": value,
                        "timeOfSample": get_utc_timestamp(),
                        "uncertaintyInMilliseconds": 500
                    }
                ]
            },
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "Response",
                    "payloadVersion": "3",
                    "messageId": get_uuid(),
                    "correlationToken": request["directive"]["header"]["correlationToken"]
                },
                "endpoint": {
                    "scope": {
                        "type": "BearerToken",
                        "token": "access-token-from-Amazon"
                    },
                    "endpointId": request["directive"]["endpoint"]["endpointId"]
                },
                "payload": {}
            }
        }
        return response

    elif request_namespace == "Alexa.BrightnessController":
        if request_name == "SetBrightness":
            brightness = request["directive"]["payload"]["brightness"]
            if sparkDevice.connected:
                # Call cloud function
                cmd_obj = dict(cmd=3, nd=particle_node, value=brightness)
                cmd_string = json.dumps(cmd_obj)
                sparkDevice.JSONCommand(cmd_string)

            response = {
                "context": {
                    "properties": [
                        {
                            "namespace": "Alexa.BrightnessController",
                            "name": "brightness",
                            "value": brightness,
                            "timeOfSample": get_utc_timestamp(),
                            "uncertaintyInMilliseconds": 500
                        }
                    ]
                },
                "event": {
                    "header": {
                        "namespace": "Alexa",
                        "name": "Response",
                        "payloadVersion": "3",
                        "messageId": get_uuid(),
                        "correlationToken": request["directive"]["header"]["correlationToken"]
                    },
                    "endpoint": {
                        "scope": {
                            "type": "BearerToken",
                            "token": "access-token-from-Amazon"
                        },
                        "endpointId": request["directive"]["endpoint"]["endpointId"]
                    },
                    "payload": {}
                }
            }
            return response
        elif request_name == "AdjustBrightness":
            brightness = request["directive"]["payload"]["brightnessDelta"]
            # ToDo:... need new cloud interface
            response = {
                "context": {
                    "properties": [
                        {
                            "namespace": "Alexa.BrightnessController",
                            "name": "brightness",
                            "value": brightness,
                            "timeOfSample": get_utc_timestamp(),
                            "uncertaintyInMilliseconds": 500
                        }
                    ]
                },
                "event": {
                    "header": {
                        "namespace": "Alexa",
                        "name": "Response",
                        "payloadVersion": "3",
                        "messageId": get_uuid(),
                        "correlationToken": request["directive"]["header"]["correlationToken"]
                    },
                    "endpoint": {
                        "scope": {
                            "type": "BearerToken",
                            "token": "access-token-from-Amazon"
                        },
                        "endpointId": request["directive"]["endpoint"]["endpointId"]
                    },
                    "payload": {}
                }
            }
            return response

    elif request_namespace == "Alexa.ColorTemperatureController":
        # should retrieve from status change report
        cct = 5000
        if request_name == "SetColorTemperature":
            cct = request["directive"]["payload"]["colorTemperatureInKelvin"]
        elif request_name == "DecreaseColorTemperature":
            cct = cct - 200
            if cct < 3000:
                cct = 3000
        elif request_name == "IncreaseColorTemperature":
            cct = cct + 200
            if cct > 6500:
                cct = 6500

        if sparkDevice.connected:
            # Call cloud function
            cmd_obj = dict(cmd=5, nd=particle_node, value=cct)
            cmd_string = json.dumps(cmd_obj)
            sparkDevice.JSONCommand(cmd_string)

        response = {
            "context": {
                "properties": [
                    {
                        "namespace": "Alexa.ColorTemperatureController",
                        "name": "colorTemperatureInKelvin",
                        "value": cct,
                        "timeOfSample": get_utc_timestamp(),
                        "uncertaintyInMilliseconds": 500
                    }
                ]
            },
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "Response",
                    "payloadVersion": "3",
                    "messageId": get_uuid(),
                    "correlationToken": request["directive"]["header"]["correlationToken"]
                },
                "endpoint": {
                    "scope": {
                        "type": "BearerToken",
                        "token": "access-token-from-Amazon"
                    },
                    "endpointId": request["directive"]["endpoint"]["endpointId"]
                },
                "payload": {}
            }
        }
        return response

    elif request_namespace == "Alexa.ColorController":
        if request_name == "SetColor":
            # HSV to RGB
            rgb_color = [0, 255, 0, 0]
            hsv_color = request["directive"]["payload"]["color"]
            #rgb_color = colorsys.hsv_to_rgb(hsv_color)

            if sparkDevice.connected:
                # Call cloud function
                cmd_obj = dict(cmd=2, nd=particle_node)
                cmd_obj['ring'] = [0, 1, 80] + rgb_color
                cmd_string = json.dumps(cmd_obj)
                sparkDevice.JSONCommand(cmd_string)

            response = {
                "context": {
                    "properties": [
                        {
                            "namespace": "Alexa.ColorController",
                            "name": "color",
                            "value": hsv_color,
                            "timeOfSample": get_utc_timestamp(),
                            "uncertaintyInMilliseconds": 500
                        }
                    ]
                },
                "event": {
                    "header": {
                        "namespace": "Alexa",
                        "name": "Response",
                        "payloadVersion": "3",
                        "messageId": get_uuid(),
                        "correlationToken": request["directive"]["header"]["correlationToken"]
                    },
                    "endpoint": {
                        "scope": {
                            "type": "BearerToken",
                            "token": "access-token-from-Amazon"
                        },
                        "endpointId": request["directive"]["endpoint"]["endpointId"]
                    },
                    "payload": {}
                }
            }
            return response

    elif request_namespace == "Alexa.Authorization":
        if request_name == "AcceptGrant":
            response = {
                "event": {
                    "header": {
                        "namespace": "Alexa.Authorization",
                        "name": "AcceptGrant.Response",
                        "payloadVersion": "3",
                        "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4"
                    },
                    "payload": {}
                }
            }
            return response

    # other handlers omitted in this example


# v3 utility functions
def get_endpoint_from_v2_appliance(appliance):
    endpoint = {
        "endpointId": appliance["applianceId"],
        "manufacturerName": appliance["manufacturerName"],
        "friendlyName": appliance["friendlyName"],
        "description": appliance["friendlyDescription"],
        "displayCategories": [],
        "cookie": appliance["additionalApplianceDetails"],
        "capabilities": []
    }
    endpoint["displayCategories"] = get_display_categories_from_v2_appliance(appliance)
    endpoint["capabilities"] = get_capabilities_from_v2_appliance(appliance)
    return endpoint


def get_directive_version(request):
    try:
        return request["directive"]["header"]["payloadVersion"]
    except:
        try:
            return request["header"]["payloadVersion"]
        except:
            return "-1"


def get_endpoint_by_endpoint_id(endpoint_id):
    appliance = get_appliance_by_appliance_id(endpoint_id)
    if appliance:
        return get_endpoint_from_v2_appliance(appliance)
    return None


def get_display_categories_from_v2_appliance(appliance):
    model_name = appliance["modelName"]
    if model_name == "Smart Switch": displayCategories = ["SWITCH"]
    elif model_name == "Smart Light": displayCategories = ["LIGHT"]
    elif model_name == "Smart White Light": displayCategories = ["LIGHT"]
    elif model_name == "Smart Thermostat": displayCategories = ["THERMOSTAT"]
    elif model_name == "Smart Lock": displayCategories = ["SMARTLOCK"]
    elif model_name == "Smart Scene": displayCategories = ["SCENE_TRIGGER"]
    elif model_name == "Smart Activity": displayCategories = ["ACTIVITY_TRIGGER"]
    elif model_name == "Smart Camera": displayCategories = ["CAMERA"]
    else: displayCategories = ["OTHER"]
    return displayCategories


def get_capabilities_from_v2_appliance(appliance):
    model_name = appliance["modelName"]
    if model_name == 'Smart Switch':
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Light":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ColorController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "color" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ColorTemperatureController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "colorTemperatureInKelvin" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.BrightnessController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "brightness" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerLevelController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerLevel" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PercentageController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "percentage" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart White Light":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ColorTemperatureController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "colorTemperatureInKelvin" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.BrightnessController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "brightness" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerLevelController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerLevel" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PercentageController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "percentage" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Thermostat":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ThermostatController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "targetSetpoint" },
                        { "name": "thermostatMode" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.TemperatureSensor",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "temperature" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Thermostat Dual":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ThermostatController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "upperSetpoint" },
                        { "name": "lowerSetpoint" },
                        { "name": "thermostatMode" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.TemperatureSensor",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "temperature" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Lock":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.LockController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "lockState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Scene":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.SceneController",
                "version": "3",
                "supportsDeactivation": False,
                "proactivelyReported": True
            }
        ]
    elif model_name == "Smart Activity":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.SceneController",
                "version": "3",
                "supportsDeactivation": True,
                "proactivelyReported": True
            }
        ]
    elif model_name == "Smart Camera":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.CameraStreamController",
                "version": "3",
                "cameraStreamConfigurations" : [ {
                    "protocols": ["RTSP"],
                    "resolutions": [{"width":1280, "height":720}],
                    "authorizationTypes": ["NONE"],
                    "videoCodecs": ["H264"],
                    "audioCodecs": ["AAC"]
                } ]
            }
        ]
    else:
        # in this example, just return simple on/off capability
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]

    # additional capabilities that are required for each endpoint
    endpoint_health_capability = {
        "type": "AlexaInterface",
        "interface": "Alexa.EndpointHealth",
        "version": "3",
        "properties": {
            "supported":[
                { "name":"connectivity" }
            ],
            "proactivelyReported": True,
            "retrievable": True
        }
    }
    alexa_interface_capability = {
        "type": "AlexaInterface",
        "interface": "Alexa",
        "version": "3"
    }
    capabilities.append(endpoint_health_capability)
    capabilities.append(alexa_interface_capability)
    return capabilities


def get_directive_deviceid(request):
    try:
        return request["directive"]["endpoint"]["cookie"]["deviceId"]
    except:
        try:
            return request["payload"]["appliance"]["additionalApplianceDetails"]["deviceId"]
        except:
            return PARTICLE_DEVICE_ID


def get_directive_nodeid(request):
    try:
        return int(request["directive"]["endpoint"]["cookie"]["nodeId"])
    except:
        try:
            return int(request["payload"]["appliance"]["additionalApplianceDetails"]["nodeId"])
        except:
            return int(PARTICLE_NODE_MAIN)


def get_directive_model(request):
    try:
        appliance_id = request["directive"]["endpoint"]["endpointId"]
    except:
        try:
            appliance_id = request["payload"]["appliance"]["applianceId"]
        except:
            appliance_id = SAMPLE_APPLIANCES[0]["applianceId"]

    appliance = get_appliance_by_appliance_id(appliance_id)
    if appliance is None:
        return PARTICLE_DEFAULT_MODEL
    else:
        return appliance["modelName"]

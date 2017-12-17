from config import PARTICLE_DEVICE_ID, PARTICLE_NODE_MAIN, PARTICLE_NODE_SECOND, PARTICLE_NODE_KM

# To simplify this sample Lambda, we omit validation of access tokens and retrieval of a specific
# user's appliances. Instead, this array includes a variety of virtual appliances in v2 API syntax,
# and will be used to demonstrate transformation between v2 appliances and v3 endpoints.
SAMPLE_APPLIANCES = [
    {
        "applianceId": "node_" + PARTICLE_NODE_KM,
        "manufacturerName": "Xlight",
        "modelName": "Smart Switch",
        "version": "1",
        "friendlyName": "Switch",
        "friendlyDescription": "001 Switch that can only be turned on/off",
        "isReachable": True,
        "actions": [
            "turnOn",
            "turnOff"
        ],
        "additionalApplianceDetails": {
            "deviceId": PARTICLE_DEVICE_ID,
            "nodeId": PARTICLE_NODE_KM
        }
    },
    {
        "applianceId": "node_" + PARTICLE_NODE_MAIN,
        "manufacturerName": "Xlight",
        "modelName": "Smart Light",
        "version": "1",
        "friendlyName": "Rainbow",
        "friendlyDescription": "002 Light (Rainbow) that is dimmable and can change color and color temperature",
        "isReachable": True,
        "actions": [
            "turnOn",
            "turnOff",
            "setPercentage",
            "incrementPercentage",
            "decrementPercentage",
            "setColor",
            "setColorTemperature",
            "incrementColorTemperature",
            "decrementColorTemperature"
        ],
        "additionalApplianceDetails": {
            "deviceId": PARTICLE_DEVICE_ID,
            "nodeId": PARTICLE_NODE_KM
        }
    },
    {
        "applianceId": "node_" + PARTICLE_NODE_SECOND,
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart White Light",
        "version": "1",
        "friendlyName": "Sunny",
        "friendlyDescription": "003 Light (Sunny) that is dimmable and can change color temperature only",
        "isReachable": True,
        "actions": [
            "turnOn",
            "turnOff",
            "setPercentage",
            "incrementPercentage",
            "decrementPercentage",
            "setColorTemperature",
            "incrementColorTemperature",
            "decrementColorTemperature"
        ],
        "additionalApplianceDetails": {
            "deviceId": PARTICLE_DEVICE_ID,
            "nodeId": PARTICLE_NODE_KM
        }
    }
]
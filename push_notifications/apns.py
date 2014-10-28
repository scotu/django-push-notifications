"""
Apple Push Notification Service
Documentation is available on the iOS Developer Library:
https://developer.apple.com/library/ios/#documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/ApplePushService/ApplePushService.html
"""

import json
import struct
from binascii import unhexlify
from django.conf import settings
from . import NotificationError, PUSH_NOTIFICATIONS_SETTINGS as SETTINGS


class APNSError(NotificationError):
    pass


class APNSDataOverflow(APNSError):
    pass


SETTINGS.setdefault("APNS_PORT", 2195)
if settings.DEBUG:
    SETTINGS.setdefault("APNS_HOST", "gateway.sandbox.push.apple.com")
else:
    SETTINGS.setdefault("APNS_HOST", "gateway.push.apple.com")

APNS_MAX_NOTIFICATION_SIZE = 256


def _apns_create_socket():
    import ssl
    from socket import socket
    from django.core.exceptions import ImproperlyConfigured

    sock = socket()
    certfile = SETTINGS.get("APNS_CERTIFICATE")
    if not certfile:
        raise ImproperlyConfigured(
            'You need to set PUSH_NOTIFICATIONS_SETTINGS["APNS_CERTIFICATE"] to send messages through APNS.')

    sock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_TLSv1, certfile=certfile)
    sock.connect((SETTINGS["APNS_HOST"], SETTINGS["APNS_PORT"]))

    return sock


def _apns_pack_message(token, data):
    format = "!cH32sH%ds" % (len(data))
    return struct.pack(format, b"\0", 32, unhexlify(token), len(data), data)


def _apns_send(token, data, badge=0, sound="chime", content_available=False, custom_params={}, action_loc_key=None,
               loc_key=None, loc_args=[], socket=None):
    # data = {}
    #alert = {}

    #	if action_loc_key or loc_key or loc_args:
    #		alert = {} #{"body": alert}
    #		if action_loc_key:
    #			alert["action-loc-key"] = action_loc_key
    #		if loc_key:
    #			alert["loc-key"] = loc_key
    #		if loc_args:
    #			alert["loc-args"] = loc_args

    #data["alert"] = alert

    #	if badge:
    #		data["badge"] = badge
    #
    #	if sound:
    #		data["sound"] = sound
    #
    #	if content_available:
    #		data["content-available"] = 1

    # convert to json, avoiding unnecessary whitespace with sepatators
    #data = json.dumps({"aps": data, "content": content}, separators=(",",":"))
    #data = json.dumps(data, separators=(",",":"))
    if len(data) > APNS_MAX_NOTIFICATION_SIZE:
        raise APNSDataOverflow("Notification body cannot exceed %i bytes" % (APNS_MAX_NOTIFICATION_SIZE))

    data = _apns_pack_message(token, data)

    if socket:
        socket.write(data)
    else:
        socket = _apns_create_socket()
        socket.write(data)
        socket.close()


def apns_send_message(registration_id, data, **kwargs):
    """
	Sends an APNS notification to a single registration_id.
	This will send the notification as form data.
	If sending multiple notifications, it is more efficient to use
	apns_send_bulk_message()
	Note that \a data is sent as a string.
	"""

    return _apns_send(registration_id, json.dumps(data), **kwargs)


def apns_send_bulk_message(registration_ids, data):
    """
	Sends an APNS notification to one or more registration_ids.
	The registration_ids argument needs to be a list.
	"""
    socket = _apns_create_socket()
    for registration_id in registration_ids:
        _apns_send(registration_id, json.dumps(data), socket=socket, **kwargs)

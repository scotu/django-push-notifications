"""
Google Cloud Messaging
Previously known as C2DM
Documentation is available on the Android Developer website:
https://developer.android.com/google/gcm/index.html
"""

import urllib2
from . import NotificationError, PUSH_NOTIFICATIONS_SETTINGS as SETTINGS


SETTINGS.setdefault("GCM_POST_URL", "https://android.googleapis.com/gcm/send")

class GCMError(NotificationError):
	pass

def _gcm_send(data, content_type):
	from django.core.exceptions import ImproperlyConfigured

	key = SETTINGS.get("GCM_API_KEY")
	if not key:
		raise ImproperlyConfigured('You need to set PUSH_NOTIFICATIONS_SETTINGS["GCM_API_KEY"] to send messages through GCM.')

	headers = {
		"Content-Type": content_type,
		"Authorization": "key=%s" % (key),
		"Content-Length": str(len(data)),
	}

	request = urllib2.Request(SETTINGS["GCM_POST_URL"], data, headers)
	response = urllib2.urlopen(request)
	result = response.read()

	if result.startswith("Error="):
		raise GCMError(result)

	return result

def gcm_send_message(registration_id, data, collapse_key=None):
	"""
	Sends a GCM notification to a single registration_id.
	This will send the notification as form data.
	If sending multiple notifications, it is more efficient to use
	gcm_send_bulk_message()
	"""
	from urllib import urlencode
	#import ipdb; ipdb.set_trace()
 
	values = {
		"registration_id": registration_id,
		"collapse_key": collapse_key,
	}
	values["data.msg"] = data['msg'] #.encode("utf-8")
	values["data.content"] = data['content'] #.encode("utf-8")
	values.update(data)

	#for k, v in data.items():
	#	values["data.%s" % (k)] = v['msg'] #.encode("utf-8")
	#import ipdb; ipdb.set_trace()
	
	#values["data.contet"] = data['content'] #.encode("utf-8")
  
	data = urlencode(values)
	return _gcm_send(data, "application/x-www-form-urlencoded;charset=UTF-8")

def gcm_send_bulk_message(registration_ids, data, collapse_key=None, delay_while_idle=False):
	"""
	Sends a GCM notification to one or more registration_ids. The registration_ids
	needs to be a list.
	This will send the notification as json data.
	"""
	import json

	values = {
		"registration_ids": registration_ids,
		"collapse_key": collapse_key,
		"data": data,
	}

	if delay_while_idle:
		values["delay_while_idle"] = delay_while_idle

	data = json.dumps(values)
	return _gcm_send(data, "application/json")

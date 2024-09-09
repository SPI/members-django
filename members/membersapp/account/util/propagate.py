from django.conf import settings
from django.http import JsonResponse

import hmac
import base64
import json
from hashlib import sha512
import requests

from membersapp.account.models import CommunityAuthSite, SecondaryEmail
from membersapp.app.models import Members


def send_change_to_apps(user, status=False):
    sites = CommunityAuthSite.objects.all()
    for site in sites:
        if site.push_changes:
            if status:
                data = {
                    "type": "update",
                    "status": [{
                        "username": user.username,
                        "status": Members.object.get(pk=user.pk).get_status,
                    }]
                }
            else:
                data = {
                    "type": "update",
                    "users": [{
                        "username": user.username,
                        "email": user.email,
                        "firstname": user.first_name,
                        "lastname": user.last_name,
                        "secondaryemails": [a.email for a in SecondaryEmail.objects.filter(user=user, confirmed=True).order_by('email')],
                    }]
                }
            json_data = json.dumps(data).encode('utf-8')
            signature = hmac.new(base64.b64decode(site.cryptkey), json_data, sha512).digest()
            headers = {
                'X-pgauth-sig': base64.b64encode(signature).decode('utf-8'),
                'Content-Type': 'application/json',
            }
            try:
                response = requests.post(site.apiurl, headers=headers, data=json_data)
                response.raise_for_status()  # Raise an error for bad status codes
            except requests.exceptions.HTTPError as e:
                print("Http Error:", e)
            except requests.exceptions.ConnectionError as e:
                print("Error Connecting:", e)
            except requests.exceptions.Timeout as e:
                print("Timeout Error:", e)
            except requests.exceptions.RequestException as e:
                print("Unknown error", e)

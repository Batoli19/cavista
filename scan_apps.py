
import json
import codecs

print("Scanning for apps...")
try:
    with codecs.open('apps.json', 'r', 'utf-16') as f:
        data = json.load(f)
        
    found = False
    for app in data:
        name = app.get('Name', '').lower()
        if 'whatsapp' in name:
            print(f"FOUND WHATSAPP: {app['Name']} | ID: {app['AppID']}")
            found = True
        if 'spotify' in name:
            print(f"FOUND SPOTIFY: {app['Name']} | ID: {app['AppID']}")
            found = True
            
    if not found:
        print("Could not find WhatsApp or Spotify in the Start Menu list.")
        
except Exception as e:
    print(f"Error reading apps.json: {e}")

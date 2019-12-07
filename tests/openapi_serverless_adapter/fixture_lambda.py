def handle_get_pet(event, *_):
    return {
               "id": event['pathParameters']['petId'],
               "name": "petname",
               "photoUrls": ["http://url.com/a.jpg"]
           }, 200

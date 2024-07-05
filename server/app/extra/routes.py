
from flask import Blueprint, jsonify
import requests
# if need to handle PDF download in the backend
# from weasyprint import HTML     # print PDF: need dependencies >> brew install cairo pango gdk-pixbuf libffi


extra_bp = Blueprint('extra', __name__)

@extra_bp.route('/api/exchange_rate', methods=['GET'])
def get_exchange_rate():

    endpoint = 'latest'
    access_key = '41f3aa2c148201fc12542c1ce270f6a6'

    # define url for api call, you can find on the website document as well 
    url = f'https://api.exchangeratesapi.io/v1/{endpoint}?access_key={access_key}&base=EUR&symbols=CNY,JPY,USD,CAD'
    # get that response
    url_response = requests.get(url)
    json_response = url_response.json()

    if json_response['success']:
        return jsonify(json_response)
    return jsonify({"message": "subscription might have expired"}), 200




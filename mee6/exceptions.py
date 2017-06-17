from json.decoder import JSONDecodeError

class APIException(Exception):
    def __init__(self, r):
        msg = 'Request failed status_code={} payload={}'.format(r.status_code,
                                                                r.text)
        try:
            decoded_payload = r.json()
        except JSONDecodeError:
            decoded_payload = {}

        self.payload = r.text
        self.status_code = r.status_code
        self.error_code = decoded_payload.get('code')
        self.error_message = decoded_payload.get('message')

        super(APIException, self).__init__(msg)


class RPCException(Exception):
    def __init__(self, r):
        msg = 'Request failed status_code={} payload={}'.format(r.status_code,
                                                                r.text)
        self.payload = r.text
        self.status_code = r.status_code

        super(RPCException, self).__init__(msg)


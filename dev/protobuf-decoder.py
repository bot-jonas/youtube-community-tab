import sys
from protobuf_decoder.protobuf_decoder import Parser
import base64
import json

test_target = base64.urlsafe_b64decode(sys.argv[1].replace("%3D", "=")).hex()
parsed_data = Parser().parse(test_target)

print(json.dumps(parsed_data.to_dict(), indent=4))

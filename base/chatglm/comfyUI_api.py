# This is an example that uses the websockets api to know when a prompt execution is done
# Once the prompt execution is done it downloads the images using the /history endpoint

import io
import json
import random
import urllib
import uuid

import requests
# NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import websocket
from PIL import Image


class ComfyUIApi():
    def __init__(self, server_address="127.0.0.1:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = websocket.WebSocket()
        self.ws.connect(
            "ws://{}/ws?clientId={}".format(server_address, self.client_id))

    def queue_prompt(self, prompt):
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = requests.post(
            "http://{}/prompt".format(self.server_address), data=data)
        print(req.text)
        return json.loads(req.text)

    def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename,
                "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with requests.get("http://{}/view?{}".format(self.server_address, url_values)) as response:
            image = Image.open(io.BytesIO(response.content))
            return image

    def get_image_url(self, filename, subfolder, folder_type):
        data = {"filename": filename,
                "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        return "http://{}/view?{}".format(self.server_address, url_values)

    def get_history(self, prompt_id):
        with requests.get("http://{}/history/{}".format(self.server_address, prompt_id)) as response:
            return json.loads(response.text)

    def get_images(self, prompt, isUrl=False):
        prompt_id = self.queue_prompt(prompt)['prompt_id']
        output_images = []
        while True:
            out = self.ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break  # Execution is done
            else:
                continue  # previews are binary data

        history = self.get_history(prompt_id)[prompt_id]
        for o in history['outputs']:
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]
                if 'images' in node_output:
                    for image in node_output['images']:
                        image_data = self.get_image_url(image['filename'], image['subfolder'], image['type']) if isUrl else self.get_image(
                            image['filename'], image['subfolder'], image['type'])
                        image['image'] = image_data
                        output_images.append(image)

        return output_images


prompt_text = """
{
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "cfg": 8,
            "denoise": 1,
            "latent_image": [
                "5",
                0
            ],
            "model": [
                "4",
                0
            ],
            "negative": [
                "7",
                0
            ],
            "positive": [
                "6",
                0
            ],
            "sampler_name": "euler",
            "scheduler": "normal",
            "seed": 8566257,
            "steps": 20
        }
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": "chilloutmix_NiPrunedFp32Fix.safetensors"
        }
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "batch_size": 1,
            "height": 512,
            "width": 512
        }
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": [
                "4",
                1
            ],
            "text": "masterpiece best quality girl"
        }
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": [
                "4",
                1
            ],
            "text": "bad hands"
        }
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": [
                "3",
                0
            ],
            "vae": [
                "4",
                2
            ]
        }
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "ComfyUI",
            "images": [
                "8",
                0
            ]
        }
    }
}
"""
if __name__ == '__main__':
    prompt = json.loads(prompt_text)
    # set the text prompt for our positive CLIPTextEncode
    prompt["6"]["inputs"]["text"] = "masterpiece best quality man"

    # set the seed for our KSampler node
    prompt["3"]["inputs"]["seed"] = ''.join(
        random.sample('123456789012345678901234567890', 14))

    cfui = ComfyUIApi()
    images = cfui.get_images(prompt)

    # Commented out code to display the output images:

    for node_id in images:
        for image_data in images[node_id]:
            import io

            from PIL import Image
            image = Image.open(io.BytesIO(image_data))
            image.show()

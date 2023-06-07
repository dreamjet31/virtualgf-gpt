import base64
from io import BytesIO

import gradio as gr
import torch
from transformers import BlipForConditionalGeneration, BlipProcessor

from modules import chat, shared
from modules.ui import gather_interface_values

# If 'state' is True, will hijack the next chat generation with
# custom input text given by 'value' in the format [text, visible_text]
input_hijack = {
    'state': False,
    'value': ["", ""]
}

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base", torch_dtype=torch.float32).to("cpu")


def caption_image(raw_image):
    inputs = processor(raw_image.convert('RGB'), return_tensors="pt").to("cpu", torch.float32)
    out = model.generate(**inputs, max_new_tokens=100)
    return processor.decode(out[0], skip_special_tokens=True)


def generate_chat_picture(picture, name1, name2):
    text = f'*{name1} sends {name2} a picture that contains the following: “{caption_image(picture)}”*'
    # lower the resolution of sent images for the chat, otherwise the log size gets out of control quickly with all the base64 values in visible history
    picture.thumbnail((300, 300))
    buffer = BytesIO()
    picture.save(buffer, format="JPEG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    visible_text = f'<img src="data:image/jpeg;base64,{img_str}" alt="{text}">'
    return text, visible_text


def ui():
    picture_select = gr.Image(label='Send a picture', type='pil')

    # Prepare the input hijack, update the interface values, call the generation function, and clear the picture
    picture_select.upload(
        lambda picture, name1, name2: input_hijack.update({"state": True, "value": generate_chat_picture(picture, name1, name2)}), [picture_select, shared.gradio['name1'], shared.gradio['name2']], None).then(
        gather_interface_values, [shared.gradio[k] for k in shared.input_elements], shared.gradio['interface_state']).then(
        chat.cai_chatbot_wrapper, shared.input_params, shared.gradio['display'], show_progress=False).then(
        lambda: None, None, picture_select, show_progress=False)

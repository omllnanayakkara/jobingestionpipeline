from paddleocr import PaddleOCR
import ollama
import json
from models.job_listing import JobCategory, JobType

def ocr():
    ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False
)

    result = ocr.predict("image2.png")

    for page in result:
        for line in page["rec_texts"]:
            print(line)



# template = {
#     "title": "verbatim-string",
#     "date": "date-time",
#     "total": "number",
#     "payment_method": "verbatim-string",
# }

def vlm():
    response = ollama.chat(
        model="numind/nuextract3:q4_k_m",
        messages = [
            {"role": "mode", "content": "content"},
            {
                "role": "user",
                "content": "",
                "images": ["image2.png"],
            },
        ]
        ,
        think=False,
        options={
            "temperature": 0.2,
            "top_k": 0.8
        },
        keep_alive=0
    )
    print(response.message.content)

def _enum_values(enum_cls) -> list[str]:
    return [member.value for member in enum_cls]

template = {
    "title": "verbatim-string",
    "description": "string",
    "job_type": _enum_values(JobType),
    "category": _enum_values(JobCategory),
    "posted_date": "date-time",
    "location": "verbatim-string",
    "company_name": "verbatim-string"
}

def vlm_templated():
    response = ollama.chat(
        model="numind/nuextract3:q4_k_m",
        messages = [
            {"role": "template", "content": json.dumps(template, indent=4)},
            {
                "role": "user",
                "content": "",
                "images": ["image2.png"],
            },
        ]
        ,
        think=False,
        options={
            "temperature": 0.2,
            "top_k": 0.8
        },
        keep_alive=0
    )
    print(response.message.content)



print("OCR==================")
ocr()

print("VLM==================")
vlm()

print("VLM Templated==================")
vlm_templated()
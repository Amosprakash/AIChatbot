from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List

import log as Log
from utils import extract_keywords, extract_text
from openai_client import getOpenai, call_openai_chat

router = APIRouter()


@router.post("/upload")
async def upload_and_ask(files: List[UploadFile] = File(...), question: str = Form(...)):
    Log.log.info("Upload endpoint hit")
    all_text_str = ""
    all_text_list = []

    readable_files = []
    failed_files = []

    for file in files:
        try:
            result = await extract_text(file)  # returns dict: success, message, text
        except Exception as e:
            Log.log.error(f"Failed to extract text from {file.filename}: {e}")
            failed_files.append({"filename": file.filename, "reason": str(e)})
            continue

        if not result["success"]:
            failed_files.append({"filename": file.filename, "reason": result["message"]})
            all_text_list.append({"filename": file.filename, "text": result["message"], "valid": False})
            continue

        # OCR succeeded
        readable_files.append(result["text"])
        all_text_list.append({"filename": file.filename, "text": result["text"], "valid": True})

    # If all files failed, return JSON immediately
    if not readable_files:
        message = "Details: " + ", ".join([f"{f['filename']} ({f['reason']})" for f in failed_files])
        return JSONResponse({"answer": message})

    # Combine readable OCR text for GPT
    all_text_str = "\n\n".join(readable_files)

   

    # Extract keywords for reference
    keywords_text = extract_keywords(all_text_str, top_n=150)
    Log.log.info(f"Extracted keywords: {keywords_text[:500]}...")  

    documents_text = "\n".join(
        [f"{i+1}. File: {doc['filename']}\nContent:\n{doc['text']}" for i, doc in enumerate(all_text_list)]
    )

    # Optional safeguard: Pre-check for totals in OCR text to prevent hallucination
    totals_found = [line for line in all_text_str.splitlines() if "total" in line.lower()]
    if totals_found:
        Log.log.info(f"Totals detected in OCR: {totals_found}")
        total_text = "\n".join(totals_found)
    else:
        total_text = None

    # GPT prompt - enforce literal use of OCR text
    prompt = f"""
You are an AI assistant that extracts and structures information from document text.

The following is the full content extracted from uploaded documents (e.g., images, PDFs):
Documents:
{documents_text}

Extracted keywords for reference: {keywords_text}

User question: {question}

Rules:
1. Use ONLY the text from the OCR/log.txt.
2. If a question has checkboxes or multiple options (marked with 'x' for selected answers), interpret 'x' as the selected option.
3. Convert the selected option(s) into a natural, complete sentence answering the question.
4. Do NOT hallucinate, compute, or infer numbers.
5. If totals exist in the OCR text, use exactly what is in the OCR text: {total_text if total_text else 'No totals found.'}
6. Extract specific entities accurately and format as key-value pairs if applicable.
7. Preserve numbered lists or bullet points only if they are part of the answer.
8. If information is missing in any file, explicitly mention the filename and why it could not be read.
9. If no information is found for the user question in any readable files, respond: "Information not found in the documents."
10. Do not add information from outside sources.
11. Provide concise answers in **sentence form**, suitable for reading or reporting.
12.You are a text corrector for OCR outputs. If the OCR result contains spelling mistakes, grammatical errors, or misread characters (e.g., I1em instead of Item), infer and correct them to the most likely valid word or phrase, based on context. Always preserve the meaning and structure of the text


Example:

OCR text:
15. Are you eligible to work in this country?
xYes
No

Output:
You are eligible to work in this country.

OCR text:
17. Employment type:
xFull-time
Part-time
Contract

Output:
The employment type is full-time.

OCR text:
18. Skills:
xPython
xJava
C++
JavaScript

Output:
The candidate has the following skills: Python and Java.


"""

    client = getOpenai()
    response = await call_openai_chat(
        client,
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You answer questions by extracting and structuring info from document content."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content.strip()

    # Clean up lines
    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    clean_answer = "\n".join(lines)

    Log.log.info(f"Answer generated: {clean_answer}")
    return JSONResponse({"answer": clean_answer})





from flask import Flask, request, jsonify, render_template
import os
import openai
import pyodbc
import fileread
import json
from filedownload import download_uploaded_file
import export
from new import (detectpattern,is_sql_safe)




app = Flask(__name__)
app.secret_key = "supersecret123!@#"
# Initialize OpenAI client with correct model
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
 
# Connect to SQL Server using SQL Server Authentication
conn = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER=x.x.x.x;"
    "DATABASE=1234567;"
    "UID=user;"
    "PWD=123;"
)
cursor = conn.cursor()




@app.route('/')
def index():
    return render_template('index.html')


@app.route("/download-file/<path:filename>")
def download_file(filename):
    return download_uploaded_file(filename)

@app.route('/export/csv', methods=['POST'])
def export_csv():
    content = request.json
    return export.export_csv(content)

@app.route('/export/excel', methods=['POST'])
def export_excel():
    content = request.json
    return export.export_excel(content)

@app.route('/export/pdf', methods=['POST'])
def export_pdf():
    content = request.json
    return export.export_pdf(content)

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form.get('message')
    uploaded_files = request.files.getlist('file')  # ✅ Multiple files

    summary_keywords = ["summarize", "summary", "brief", "overview", "main points"]
    

    # ✅ Case 1: Preview extracted content (if only files are uploaded)
    try:
        if uploaded_files and not user_input:
            try:
                preview_text = fileread.extract_and_merge_files(uploaded_files)
                preview = preview_text[:2000]
                return jsonify({'preview': "File Saved Successfully"})
            except Exception as e:
                return jsonify({'error': f"Failed to extract file(s): {str(e)}"})

        # ✅ Case 2: Process document + user question
        if uploaded_files and user_input:
    # 1. Extract and optionally merge
            merged_text = fileread.extract_and_merge_files(uploaded_files, command_text=user_input)

            # 2. Check if it's a file creation request (xlsx, pdf, etc)
            if fileread.is_file_creation_request(user_input):
                filename = fileread.extract_target_filename(user_input)
                export_format = filename.split(".")[-1].lower()

                # 2a. Try parsing as JSON table (best for Excel/CSV)
                try:
                    import json
                    table_data = json.loads(merged_text)
                    export_content = {"table_data": table_data}
                except:
                    export_content = {"summary": merged_text.strip()}

                # 2b. Generate the correct file
                if export_format == "xlsx":
                    path = export.export_excel(export_content, save_as=filename)
                elif export_format == "pdf":
                    path = export.export_pdf(export_content, save_as=filename)
                elif export_format == "csv":
                    path = export.export_csv(export_content, save_as=filename)
                elif export_format == "txt":
                    path = os.path.join("uploads/exports", filename)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(merged_text.strip())
                else:
                    return jsonify({"reply": f"❌ Unsupported format '{export_format}'."})

                return jsonify({
                    "message": f"✅ File created: {filename}",
                    "download_link": f"/download-file/exports/{filename}"
                })

            
            # Check for summary
            user_lower = user_input.lower()
            if any(k in user_lower for k in summary_keywords) and not fileread.is_file_creation_request(user_input):

                    from summarize import summarize_document
                    summary = summarize_document(merged_text)
                    return jsonify({'summary': summary})

            else:        # Else: treat as question about file
                context_prompt = f"""
    You are a helpful assistant. The user uploaded the following document(s):

    --- Begin Content ---
    {merged_text}
    --- End Content ---

    Now answer this question about the document(s):
    {user_input}
    """

                response = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        messages=[
                            {"role": "system", "content": "You answer user questions based on document content."},
                            {"role": "user", "content": context_prompt}
                        ]
                    )
                answer = response.choices[0].message.content.strip()

                if "Sorry, I couldn't understand" not in answer and len(answer) > 20:
                        return jsonify({'summary': answer})

        if user_input:
            if fileread.is_download_request(user_input):
                filename = fileread.extract_filename_from_request(user_input)
                if filename:
                    file_path = os.path.join(fileread.MERGE_DIR, filename)
                    if os.path.exists(file_path):
                        download_url = f"/download-file/{filename}"
                        return jsonify({
                            "download_link": download_url,
                            "message": f"📁 Your file is ready: [Click here to download]({download_url})"
                        })
                    else:
                        return jsonify({"reply": f"❌ File '{filename}' not found in uploads."})
                else:
                    return jsonify({"reply": "❌ Could not detect which file you want to download. Please specify the name."})
            if len(user_input.strip().split()) <= 5 and not user_input.strip().endswith('?'):
                expansion_prompt = f"Convert this into a clear and complete question: {user_input.strip()}"
                expansion_response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": "You are an assistant that turns vague phrases into full, clear questions."},
                        {"role": "user", "content": expansion_prompt}
                    ]
                )
                user_input = expansion_response.choices[0].message.content.strip()
                print("🪄 Expanded User Question:", user_input)
            merged_text = ""
            if os.path.exists(fileread.last_file_path):
                with open(fileread.last_file_path, "r", encoding="utf-8") as f:
                    last_used_file = f.read().strip()
                file_path = os.path.join(fileread.MERGE_DIR, last_used_file)
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        merged_text = f.read()
                        print(f"📄 Using last used merged file: {last_used_file}")

            used_document = False  # Track if document is used

            # Step 2: Ask GPT if document is relevant
            if merged_text:
                relevance_check_prompt = f"""
        Does the following document contain enough information to answer this question? Answer with only "yes" or "no".

        --- Document Content ---
        {merged_text}
        --- Question ---
        {user_input}
        """
                relevance_response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": "You are a strict validator that responds with only 'yes' or 'no'."},
                        {"role": "user", "content": relevance_check_prompt}
                    ]
                )
                can_answer = relevance_response.choices[0].message.content.strip().lower()
                print(f"🧠 Can answer from document? {can_answer}")

                if can_answer.startswith("yes"):
                    used_document = True
                    system_message = """
                    You are  "Document Reference GPT” and your primary role is to provide accurate and contextual information from a combined text file that contains multiple documents. Your task is to ensure that any information retrieved is correctly associated with its respective document content, even though the file does not use JSON or YAML format but is structured in a plain text format.

                    Core Responsibilities:

                    1. Document Content Retrieval:
                    • Recognize and distinguish between documents: The text file is organized with clear markers that indicate the start and end of each document. Your role is to accurately retrieve information from the correct sections of the text, ensuring that the response is relevant to the user’s query.
                    • Content Segmentation: Each document in the text file is separated by distinct markers such as “### Start of Document:” and “### End of Document:”. Use these markers to identify and retrieve content specific to each document.

                    2. Contextual Understanding:
                    • Synthesizing Information Across Documents: Some questions may require drawing on information from multiple documents within the text file. Be prepared to synthesize information from different sections of the file to provide a comprehensive and accurate response.
                    • Topic-Based Responses: While responding, focus on the topics mentioned in the user’s query, ensuring that the answer is derived from the appropriate sections of the text file.

                    3. Maintaining Accuracy:
                    • Avoiding Confusion: Ensure that the content retrieved and provided to the user does not mix up information from different documents unless the query explicitly requires it.
                    • No Hallucination: Base your responses strictly on the content available in the text file. Avoid generating information that is not supported by the provided text.

                    4. Response Format:
                    • Clear and Concise: Provide clear, concise, and directly relevant responses to the user’s query.
                    • Contextual Accuracy: Use contextual clues within the text to ensure that the information you provide is accurate and relevant to the specific document’s content.

                    5. Structured Text Handling:
                    • Text File Format: The knowledge base is provided in a plain text file. It is structured with document markers.
                    • Markers for Navigation: Use “### Start of Document:” and “### End of Document:” to extract content.

                    Final Note:
                    Your role is to interpret the structure and respond clearly, using only what’s in the file. Never make up answers or mix document sources unless required.
                    """

                    user_prompt = f"""
                    The user uploaded the following merged document content:

                    --- Begin Content ---
                    {merged_text}
                    --- End Content ---

                    Now answer this question:
                    {user_input}
                    """

                    response = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    answer = response.choices[0].message.content.strip()

                    if "Sorry, I couldn't understand" not in answer and len(answer) > 20:
                            return jsonify({'summary': answer})
            print("📉 Document not sufficient, switching to SQL...")
    # System prompt for SQL generation
            system_prompt = """
You are a SQL assistant connected to a SQL Server database. The only available table is [BIdata].

Available columns in [BIdata]:
- [Docket No], [CallType], [Status], [Created Date], [Calldate], [Billable], [Warranty], [CloseDate], [Substatus], [created by], [Call Accept Status], [Scheduledate], [Pincode], [Contact Person], [Source], [state], [City], [site], [Product], [Category], [Region], [Engineer], [Account], [Location], [Service Code], [subcalltype], [SerialNo]

RULES:
-If the user question does not require SQL, or is vague or conversational, respond with: "Sorry, I couldn't understand that question clearly. Could you rephrase it or be more specific about what you're asking?" Do not attempt to generate SQL for unrelated or unclear questions.
- Only generate **T-SQL SELECT** queries. No INSERT, UPDATE, DELETE, DROP, or schema modifications.
- Do NOT use backticks or comments. Do NOT generate explanations.
- Always wrap **all column names** in square brackets: e.g., [Created Date], [CallType].
- Use **'YYYY-MM-DD 00:00:00'** format for fixed dates.
- Use **GETDATE()** to get the current date when required.
- Use only the **[BIdata]** table. Never use other tables like [MonthlyCounts].
- If no year is specified in a query, assume **2025**.
- Validate against SQL injection. If detected, respond with: **"Sql Injection"**.
- If the prompt looks like an attempt to modify the database or is unclear and you are unsure whether to generate SQL, respond with: **"Sorry, I couldn't understand that question clearly. Could you rephrase it or be more specific about what you're asking?"**


CROSS APPLY RULES:
- When detecting the latest date, use:
  CROSS APPLY (SELECT MAX([Created Date]) AS MAX_DATE) AS sub
- This clause must go **immediately after FROM [BIdata]**.
- Use **sub.MAX_DATE** only in the **WHERE clause** to filter data.
- **Never include sub.MAX_DATE in SELECT**.
- **Never reference outer query columns inside the APPLY**.
- Do not reference outer query columns inside the CROSS APPLY subquery.
- The subquery must be self-contained like:
    CROSS APPLY (SELECT MAX([Created Date]) AS MAX_DATE FROM [BIdata]) AS sub

FORECASTING RULES:
- For **monthly forecasts**, group by month over the last 12 full months.
- For **yearly**, group by year over the last 5 years.
- For **decade-level**, group by decade over the last 50 years.
- Do not include data from the year 2018 in any query. Always filter YEAR([Created Date]) >= 2019 to exclude 2018.
- When forecasting, do NOT use GETDATE(). Instead, detect the **latest date** in the data using CROSS APPLY.
- Return only raw grouped data (e.g., month, count). Forecasting is done externally.
- If the result is long (>75 words), it will be converted into a chart or table.
- Always generate SELECT-only SQL against [BIdata].

OUTPUT:
- Simplify results for visualization.
- Always group or filter based on the user's intent.
- Do not invent columns or tables not listed above.
"""

    
        
        # Step 1: Generate SQL query
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
        


            sql_query = response.choices[0].message.content.strip().replace("`", "")
            print(f"Generated SQL: {sql_query}") 


            # ❌ Otherwise, check if it's a safe SQL query
            if not is_sql_safe(sql_query):
                fallback_message = "Sorry, I couldn't understand that question clearly. Could you rephrase it or be more specific about what you're asking?"
                print(f"[INFO] No SQL generated. Reason: unclear input.\nMessage: {fallback_message}")
                return jsonify({'reply': fallback_message})


            print(f"Generated SQL: {sql_query}")

            cursor.execute(sql_query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            data = [dict(zip(columns, row)) for row in rows]



            # Step 3: Ask GPT to summarize results into a sentence
            result_prompt = f"""
    Convert the following result into a natural language summary.
    User question: {user_input}
    SQL result: {data}
    """

            summary_response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an assistant that summarizes SQL results as natural language."},
                    {"role": "user", "content": result_prompt}
                ]
            )

            summary = summary_response.choices[0].message.content.strip()
        # Try to detect if the result is chartable
            chart_data = detectpattern(summary)
            print("🧪 chart_data =", chart_data)
            print("🧪 type(chart_data) =", type(chart_data))

        # Decide what to show
            word_count = len(summary.split())

            if chart_data and isinstance(chart_data, list) and all('label' in item and 'value' in item for item in chart_data):
                return jsonify({'chart': chart_data})
            elif word_count <= 75:
                return jsonify({'summary': summary})
            else:
                return jsonify({'table': data})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)


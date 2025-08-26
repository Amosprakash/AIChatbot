import openai
import os
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Chunk The Text for Summarize
def chunk_text(text, max_words=700):
    words = text.split()
    return [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

def summarize_with_gpt(text):
    prompt = f"Summarize the following document content in clear and concise language:\n\n{text}\n\nSummary:"

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
            {"role": "user", "content": prompt}
        ]
    )
    answer = response.choices[0].message.content.strip()
    return answer
# Summarize the Content in Document
def summarize_document(full_text):
    chunks = chunk_text(full_text)
    partial_summaries = [summarize_with_gpt(chunk) for chunk in chunks]

    if len(partial_summaries) > 1:
        # Summarize the summaries
        return summarize_with_gpt(" ".join(partial_summaries))
    elif partial_summaries:
        return partial_summaries[0]
    else:
        return "No content to summarize."

from langchain_groq import ChatGroq

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

response = llm.invoke("Say hello and confirm you're working.")
print(response.content)
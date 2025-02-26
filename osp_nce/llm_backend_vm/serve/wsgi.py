import DataBaseCreator from libs.databasecreator
import RAGRetriever from libs.retriever
import Generator from libs.generator 
import ModelLoader from libs.model_loader

db_creator = DataBaseCreator()
retriever = RAGRetriever()
generator = Generator() 
model_loader = ModelLoader()
 

app = FastAPI() 

@app.get("/retrieve/")
async def retrieve():
    params = {document_json, query, model_choice}
    model = model_loader.load(model_choice)
    db_creater.model = model
    document_db = db_creator.create(document_json)
    retriever.db = document_db
    relevant_docs = retriever.retrieve(query)
    return {relevant_docs}

@app.get("/chat")
async def chat():
    params = {prompt_str, model_choice}
    model = model_loader.load(model_choice)
    generator.model = model
    answer = generator.invoke(prompt_str)
    return answer

@app.get("/load_model")
async def add_model():
    params = {model_name_on_hugging_face}
    model_loader.download(model_name_on_hugging_face)
    return {"status": status}


## MOCKUP STREAMLIT INTERACTION
# -> User uploads document

# pdf.read(document)
# json serialization code 

# relevant_docs = requests.get("vm_endpoint/retrieve", {serialized_json, query})

# Render docs (Please select the most relevant page)

# Prompt Processing 
# prompt_str = System Prompt + relevant_docs + query + (Any chat history we want to send)
# answer = requests.get("vm_endpoint/chat", {prompt_str})

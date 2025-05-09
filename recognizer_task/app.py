import streamlit as st
import speech_recognition as sr
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain.prompts import MessagesPlaceholder,ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import pyttsx3
import pythoncom
import threading
import pronouncing
import json 

pythoncom.CoInitialize()
file_path = Path(__file__).parent/"First_Name.db"
connection = sqlite3.connect(file_path)
cursor=connection.cursor()
def speak_text(text):
    def run():
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run).start()

def record_audio():
    with sr.Microphone() as source:
        st.write("Speaking...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            if text:
                return text
        except Exception as e:
            st.warning("Please Provide Input Through Voice Command")
            st.empty()
            return None
def load_name_dict():
    name_dict.clear()
    data = cursor.execute("SELECT * FROM NAMES_CODE")
    for row in data:
        name_dict[row[0].lower()] = json.loads(row[1])
        
recognizer = sr.Recognizer()
name_dict={}
load_name_dict()

llm=ChatOpenAI(model='gpt-4',temperature=0.7)
prompt = ChatPromptTemplate.from_messages([
    ("system", 
    "You are a helpful assistant. Help identify the user's name by asking clarifying questions only. Do NOT include greetings, formalities, or phrases like 'How can I help you?'.from suggestion if user want to tell that my name contain this instead of this then verify it and then if uncertainity is there then spell name full Once the name is confidently identified, respond ONLY in this format:\n\n Name: name"),

    MessagesPlaceholder(variable_name="history"),
    
    ("human", 
    """Hi! I think I heard your name, and here are a few suggestions based on that:

    Could you please spell your name out loud for me?
    Once you spell it, I’ll take that as your correct name — no need to confirm again.

    You said: {speech}""")
    ])


output_pars = StrOutputParser()
chain = prompt|llm|output_pars


st.title("Name Recognizer")



if "messages" not in st.session_state:
    st.session_state['messages']=[
        {'role':'ai','content':f"Hii Speak Your First Name!"}
    ]

for msg in st.session_state.messages:
    if msg['role']=='ai':
        with st.chat_message(msg['role']):
            st.write(msg['content'])


suggestions=[]
if len(st.session_state.messages)==1:
    with st.sidebar:
        user_input=""
        if st.button("Speak"):  
            user_input =record_audio()
    if user_input:
        st.session_state.ui_code = pronouncing.phones_for_word(user_input)
        suggestions=[name for name,codes in name_dict.items() if st.session_state.ui_code[0] in codes]
        text = " , ".join(suggestions)  
        if text : 
            response = f".....     Suggested Name : {text} . \nCan you Spell out Your name for confirmation?"
        else :
            response="......    No Suggestions  Found? Can you Spell out Your name for confirmation?"
        with st.chat_message('ai'):
            st.write(response[5:])
            speak_text(response)
        st.session_state.messages.append({'role':'ai','content':response})
    else :
        st.empty()
        st.stop()
elif len(st.session_state.messages)>1:
    with st.sidebar:
        if st.button("Speak"):  
            user_input = record_audio()
    if user_input :
        st.session_state.messages.append({'role':'user','content':user_input})
        response = chain.invoke({'history':st.session_state.messages,'speech':user_input})
        st.session_state.messages.append({'role':'ai','content':response})
        good_response = "......{response}"
        name = response.split(':')
        if(len(name)>1):
                if name[1].lower() in name_dict:
                    pro_list = list(set(name_dict[(name[1].capitalize()).lower()] + [st.session_state.ui_code[0]]))
                    cursor.execute("UPDATE NAMES_CODE SET CODES = ? WHERE FLNAME = ?", (json.dumps(pro_list), name[1].capitalize()))
                else :
                    pro_list = [st.session_state.ui_code[0]]
                    cursor.execute("INSERT INTO NAMES_CODE (FLNAME, CODES) VALUES (?, ?)",(name[1].capitalize(),json.dumps(pro_list)))
                connection.commit()

                name_dict.clear()
                load_name_dict()
                st.success("add into database")
        with st.chat_message('ai'):
            st.write(response)
            speak_text(response)
connection.close()



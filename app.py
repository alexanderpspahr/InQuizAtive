import streamlit as st
from io import StringIO
from io import BytesIO
import openai
import os
from dotenv import load_dotenv
import json
from tqdm.auto import tqdm
import textwrap
from streamlit_card import card
import random
import pdfminer.high_level as pdm
import tempfile
from html.parser import HTMLParser

function = [
	{
		"name": "flashcards",
		"description": "Flashcard for a user to evaluate their understanding of a text.",
		"parameters": {
			"type": "object",
			"properties": {
				# "text_to_summarize": {
				# 	"type": "string",
				# 	"description": "This text contains the information to be summarized and used for generating questions. It may be used to create answers but you may also use general knowledge.",
				# },
				"cards":{
					"type": "array",
					"items": {
						"type":"object",
						"properties":{
							"question": {
								"type": "object",
								"properties":{
									"difficulty": {
										"type": "string",
										"enum": ["beginner", "novice", "intermediary", "expert", "omniscient"],
										"description": "This is the difficulty rating of the provided question.",
									},
									"variety": {
										"type": "array",
										"items": {
											"type": "object",
											"properties": {
												"flavor": {"type": "string"},
												"alternate_text": {"type":"string"},
											},
											"description": "This is a list of possible flavors the question could have and the alternate text of the question based on the flavor. Examples of flavor could include but are not limited to: general, funny, serious, technical, riddle. There should be more than one flavor provided.",
											"required": ["flavor", "alternate_text"],
										}
									},
									"text":{
											 "type":"string",
											 "description": "This is the question text, the variety should have alternate wordings of the question based on the flavor pairs with it in the variety array.",
									}
								},
								"description": "A question object with a possible list of flavors of the same question that are identified by the flavor as a key in the list.",
								"required": ["difficulty", "variety", "text"]
							},
							"answers": {
								"type": "object",
								"properties":{
									"format":{
										"type": "string",
										"enum": ["multiple choice", "true or false", "short answer", "fill in the blank"],
										"description": "What type of answers should be returned.",
									},
									"answer_list": {
										"type": "array",
										"items":{
											"type": "object",
											"properties": {
												"answer": {"type": "string"},
												"correct": {"type": "boolean"},
											},
											"description":"An answer, whether the answers is correct: true or false, an explanation for why the answer is correct or incorrect based on the correct value, and the context used to create the answer.",
											"required": ["answer", "correct"]
										}
									}
								},
								"description": "The answers to the question(s) provided in this response. At exactly one of the answers must be correct.",
								"required": ["format", "answer_list"]
							}
						},
						"description":"The a question generated based on the text_to_summarize and the corresponding answers.",
						"required": ["question", "answers"]
					}
				}
			},
			"description": "A list of question and answers pairs based on the summary of the text_to_summarize.",
			"required": ["cards"]
		}
	}
]

@st.cache_data
def process_content(content: str, ques_type = [], flavor = "", difficulty = []):
    true = True
    false = False
    prompt_additions = ""
    if flavor != "":
      prompt_additions += f"Generate texts with the flavor of: {flavor}."
    if any(ques_type):
      question_types = ['multple choice', 'true or false', 'short answer', 'fill in the blanks']
      chosen_question_types = []
      for chosen, qtype in zip(ques_type, question_types):
        if chosen:
          chosen_question_types += qtype

      prompt_additions += f"Generate only questions of these types: {chosen_question_types}."
    if any(difficulty):
      difficulties = ['beginner', 'novice', 'intermediate', 'expert', 'impossible']
      chosen_difficulties = []
      for chosen, diff in zip(difficulty, difficulties):
        if chosen:
          chosen_difficulties += diff
      prompt_additions += f"Generate only questions of this difficulty level: {chosen_difficulties}."

    instructions = f"Please prepare the text below for 'flashcards'. {prompt_additions} Generate a question for every important point in the summary of"
    query = instructions + "\n\n" + content

    messages = [{"role": "user", "content": query}]

    response = openai.chat.completions.create(
        # documentation: https://platform.openai.com/docs/guides/function-calling
        model="gpt-4-turbo-preview",
        messages=messages,
        temperature=0.0,
        timeout=6000,
        functions = function,
        max_tokens = 4000,
        function_call= {"name": "flashcards"} #"auto"
    )

    # print(response)

    arguments = response.choices[0].message.function_call.arguments
    # text_to_summarize = eval(arguments).get("text_to_summarize")
    cards = eval(arguments).get("cards")
    question = [eval(arguments).get("question")]
    # [
    # question
    # {
    #   difficulty enum ["beginner", "novice", "intermediary", "expert", "omniscient"]
    #   variety [flavor...]
    # }
    # {
    # answers
    #   format enum ["multiple choice", "true or false", "short answer", "fill in the blank"]
    #   answer_list [answer, correct]
    # }
    # ]

    return{
        "cards":cards,
        # "questions":question,
    }


@st.cache_data
def get_text_from_pdf(pdf):
  content = BytesIO(b"")
  pdm.extract_text_to_fp(pdf, outfp = content)
  return content




title = r'''
$\textsf{
    \Huge Welcome to In\textbf{Quiz}ative \huge
}$
'''


  
    

#Execution of app

#Execution of app

API_KEY = "placeholder"
API_KEY = st.text_input('Enter your OpenAI key here', type = "password")
os.environ['OPENAI_API_KEY'] = API_KEY
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.write(title)
col1, col2, col3 =  st.columns([1,1,1])
with col1:
  flavor = st.text_input('Flavor of text?', placeholder = 'i.e. serious, analytical, casual...')
with col2:
  st.write("Types of questions to be included:")
  question_multi_choice = st.toggle('Multiple Choice')
  question_tf = st.toggle('True or False')
  question_short_ans = st.toggle('Short Answer')
  question_fitb = st.toggle('Fill in the Blank')
  question_types = [question_multi_choice, question_tf, question_short_ans, question_fitb]
with col3:
  st.write("Difficulty levels to be included:")
  diff_beginner = st.toggle('Beginner')
  diff_novice = st.toggle('Novice')
  diff_intermediate = st.toggle('Intermediate')
  diff_expert = st.toggle('Expert')
  diff_impossible = st.toggle('Impossible :fire:')
  difficulties = [diff_beginner, diff_novice, diff_intermediate, diff_expert, diff_impossible]

file = st.file_uploader("Please choose a source for AI flashcards", type=['txt', 'pdf'])

#Change this if not debugging/testing
debug = False

#App just started, hasn't generated first questions yet:
if 'generated' not in st.session_state:
  st.session_state['generated'] = 'False'

if file is not None:
  generate_question_button = st.button("Generate Questions [:flag-ai:]", type="primary")

  if generate_question_button:
    st.session_state['generated'] = 'True'
    st.session_state['idx'] = 'not generated'
    #processing the chatgpt input and output
    file_extension = file.name.split('.')[-1]
    if file_extension == 'pdf':
      full_text = get_text_from_pdf(file).getvalue().decode("utf-8")
    else:
      stringio = StringIO(file.getvalue().decode("utf-8"))
      full_text = stringio.read()
    chunk_texts = textwrap.wrap(full_text, 10000)
    st.session_state['questions'] = []
    st.session_state['correct_answers'] = []
    for chunk in chunk_texts:
      if debug: st.write("called out to gpt4")
      result = process_content(chunk, question_types, flavor, difficulties)
      if debug: st.write(result)
      for flashcard in result["cards"]:
        answers = [answer['answer'] for answer in flashcard["answers"]["answer_list"]]
        correct_answer = "Error: no correct answer found :slightly_frowning_face:"


        #special case multiple choice append options to the choices:
        n =1
        multi_answers = []
        if flashcard['answers']['format'] =='multiple choice':
          for answer in answers:
            multi_answers.append(chr(ord('@')+n) +". " + answer)
            n += 1
          answers = multi_answers
          st.session_state['questions'].append([flashcard["question"]["text"], "Answers:"] + answers)
        elif flashcard['answers']['format'] =='true or false':
          st.session_state['questions'].append(["True or False: "+ flashcard["question"]["text"]])
        else:
          st.session_state['questions'].append([flashcard["question"]["text"]])
        for answer in flashcard["answers"]["answer_list"]:
          if answer['correct'] == True:
            correct_answer = answer['answer']
        st.session_state['correct_answers'].append(correct_answer)

  if st.session_state['generated'] == 'True':
    #question and answer loop
    if st.session_state['idx'] == 'not generated':
      st.session_state['idx'] = random.choice(range(0, len(st.session_state['questions'])))
      st.session_state['question_or_answer'] = 'question'
    col1, col2 =  st.columns([1,1])
    with col1:
      new_question_button = st.button("Choose new question", type = 'primary')
    with col2:
      answerbutton = st.button("Flip Card")
    if new_question_button:
      st.session_state['idx'] = random.choice(range(0, len(st.session_state['questions'])))
    if answerbutton and st.session_state['question_or_answer'] == 'question':
      hasClicked = card(
          title="Correct Answer:",
          text=st.session_state['correct_answers'][st.session_state['idx']],
          styles={
              "card": {
                  "width": "100%",
                  "height": "300px"
              }
          },)
      st.session_state['question_or_answer'] = 'answer'
    else:
      hasClicked = card(
        title="Question:",
        text=st.session_state['questions'][st.session_state['idx']],
        styles={
            "card": {
                "width": "100%",
                "height": "300px"
            }
        },
      )
      st.session_state['question_or_answer'] = 'question'










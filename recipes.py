import streamlit as st
from openai import OpenAI
import pandas as pd
import json
import os

def read_file(file):
    if file is not None:
        extension = os.path.splitext(file.name)[1].lower()
        if extension == ".json":
            data = json.load(file)
            return json.dumps(data, indent=2)
        elif extension == ".csv":
            data = pd.read_csv(file)
            return data.to_csv(index=False)
        else:
            return file.read()  
    return None

def read_predefined_file(file_path):
    if file_path is not None and os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    return None

def save_text(data, filename):
    with open(filename, 'w') as f:
        f.write(data)

client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

# Function to get response from OpenAI API with context
def get_openai_response(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4-0314",  # Use the gpt-4-0314 model for cost efficiency
            messages=messages,
            max_tokens=400,
            temperature=0.9,
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

# Streamlit app
def main():
    st.set_page_config(layout='wide')
    st.title('Your Recipe Assistant')

    # Read the prompt template
    prompt_template = read_predefined_file('prompt2.txt')
    if not prompt_template:
        st.error("Error reading the prompt.txt file. Please ensure it exists and is readable.")
        return

    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        gender = st.selectbox("Select your gender", ["Male", "Female"])

        age = st.number_input("Age", min_value=1, max_value=100, step=1)
        weight = st.number_input("Weight (kg)", min_value=1, max_value=200, step=1)
        height = st.number_input("Height (cm)", min_value=100, max_value=220, step=1)
        
        # Calculate TMB based on the gender, weight, height, and age
        if gender == "Male":
            TMB = 66.4730 + (13.7516 * weight) + (5.0033 * height) - (6.7550 * age)
        else:
            TMB = 655.0955 + (9.5634 * weight) + (1.8449 * height) - (4.6756 * age)

        st.write(f"Your Basal Metabolic Rate (TMB) is: {TMB:.2f} calories/day")

        activity = st.selectbox(
            "Select your level of activity",
            ["Little activity, I prefer to rest in my free time or do a hobby at home",
             "I sit most of the time during work, but I do go to the gym 3-4 times a week",
             "My workday is relatively active and I train almost everyday or at least 5 times 1 hour or more",
             "My work is active and I go once or multiple times a day to the gym"]
        )

        activity_multiplier = {
            "Little activity, I prefer to rest in my free time or do a hobby at home": 1.3,
            "I sit most of the time during work, but I do go to the gym 3-4 times a week": 1.5,
            "My workday is relatively active and I train almost everyday or at least 5 times 1 hour or more": 1.7,
            "My work is active and I go once or multiple times a day to the gym": 1.9,
        }

        activity_value = activity_multiplier[activity]
        st.write(f"Your Activity Multiplier is: {activity_value}")

        # Calculate necessary calories according to activeness
        necessary_calories = TMB * activity_value
        st.write(f"Necessary Calories according to Activeness: {necessary_calories:.2f} calories/day")

        #additional_ingredients = st.text_area("Additional Ingredients", placeholder="Enter any ingredients you have at home...")

        if st.button("Get Recipe"):
            prompt_content = prompt_template + f"\nGender: {gender}\nAge: {age}\nWeight: {weight}kg\nHeight: {height}cm\nTMB: {TMB:.2f}\nActivity Multiplier: {activity_value}\nNecessary Calories: {necessary_calories:.2f}\nAdditional considerations are the following ingredients: {additional_ingredients}"
            st.session_state['messages'].append({"role": "user", "content": prompt_content})

            response = get_openai_response(st.session_state['messages'])
            
            st.session_state['messages'].append({"role": "assistant", "content": response})
            st.experimental_rerun()

    with col2:
        if 'messages' in st.session_state:
            user_message = next((msg for msg in st.session_state['messages'] if msg["role"] == "user"), None)
            if user_message:
                st.text_area("Your Prompt:", user_message["content"], key="user_message", height=500, disabled=True)
    
    with col3:
        if 'messages' in st.session_state:
            assistant_message = next((msg for msg in st.session_state['messages'] if msg["role"] == "assistant"), None)
            if assistant_message:
                st.text_area("Generated Recipe:", assistant_message["content"], key="assistant_message", height=500, disabled=True)

if __name__ == "__main__":
    main()

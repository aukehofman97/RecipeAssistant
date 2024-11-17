import streamlit as st
from openai import OpenAI
import pandas as pd
import os

# OpenAI client initialization
client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

# Function to get response from OpenAI API
def get_openai_response(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use the gpt-4-0314 model for cost efficiency
            messages=messages,
            max_tokens=1000,
            temperature=0.9,
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

# Streamlit app
def main():
    st.set_page_config(layout='wide')
    st.title('Your Recipe Assistant and Weekly Menu Generator')

    # Tabs for different functionalities
    tab1, tab2 = st.tabs(["Calorie Calculator & Recipe Generator", "Weekly Menu Generator"])

    # Tab 1: Calorie Calculator & Recipe Generator
    with tab1:
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

            if st.button("Get Recipe"):
                prompt_content = necessary_calories
                st.session_state['messages'].append({"role": "user", "content": f'You are a recipe maker and fitness coach that helps people achieve their goals. The number of calories one needs to achieve is {prompt_content}. Create recipes for breakfast, lunch, and dinner, considering the calorie amount {prompt_content}'})
                response = get_openai_response(st.session_state['messages'])
                
                st.session_state['messages'].append({"role": "assistant", "content": response})
                st.rerun()

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

    # Tab 2: Weekly Menu Generator
    with tab2:
        st.subheader("Weekly Menu Generator")

        # Input: Days of the week
        days = st.multiselect(
            "Which days does this menu cover?",
            options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        )

        # Input: Meal type
        meal_type = st.multiselect(
            "Does this menu cover lunch, dinner, or both?",
            options=["Lunch", "Dinner"],
            default=["Lunch", "Dinner"]
        )

        # Input: Number of people
        num_people = st.number_input(
            "For how many people is this menu?",
            min_value=1,
            max_value=20,
            step=1,
            value=2
        )

        # Input: Budget
        budget = st.radio(
            "What's the date?",
            options=["End of the month", "Middle of the month", "Beginning of the month"]
        )
        
        always_buy_items = st.text_area(
            "Add items that you regularly buy independently of the menu:",
            placeholder = "E.g., milk, eggs, bread, bananas",
        )

        # Aggregate the prompt
        if st.button("Generate Menu"):
            budget_mapping = {
                "End of the month": "low-budget",
                "Middle of the month": "regular-budget",
                "Beginning of the month": "high-budget"
            }
            aggregated_prompt = (
                f"You are a meal planner. Create a {budget_mapping[budget]} weekly menu for the following details:\n"
                f"Days: {', '.join(days)}\n"
                f"Meals: {', '.join(meal_type)}\n"
                f"Number of people: {num_people}\n"
                f"Include these items in the shopping list, but not for the menu {always_buy_items}. Add them as Always Buy in the list. \n"
                f"The menu should include diverse and balanced meals, keeping the budget in mind.\n"
                f"Lunch must always contain carbohydrates like pasta/rice/couscous/similar food.\n"
                f"Dinner is all about vegetables and meat, so little carbohydrates.\n"
                f"The output should be in a table, sorted on date.\n"
                f"Give back the shopping list that considers the {num_people}"
            )
            
            # Store the initial prompt and OpenAI response in session state
            if 'menu_prompt' not in st.session_state:
                st.session_state['menu_prompt'] = aggregated_prompt
                st.session_state['menu_response'] = get_openai_response([{"role": "user", "content": aggregated_prompt}])
            
        # Feedback and refinement
        if 'menu_response' in st.session_state:
            st.markdown("### Generated Menu:")
            st.markdown(st.session_state['menu_response'])
            feedback = st.text_area("Provide feedback to refine the menu:")
            if st.button("Send Feedback"):
                feedback_prompt = (
                    f"Here is the current menu:\n{st.session_state['menu_response']}\n"
                    f"User feedback: {feedback}\n"
                    "Refine the menu accordingly and ensure it's even better."
                )
                st.session_state['menu_response'] = get_openai_response([{"role": "user", "content": feedback_prompt}])
                st.markdown("Updated Menu:", st.session_state['menu_response'])

if __name__ == "__main__":
    main()
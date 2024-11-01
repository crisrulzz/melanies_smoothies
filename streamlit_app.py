import requests
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col

# Set up page title and instructions
st.set_page_config(page_title="Smoothie Customizer", layout="centered")
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom smoothie!")

# Retrieve Snowflake connection parameters from Streamlit secrets
connection_parameters = st.secrets["connections"]["snowflake"]

# Initialize Snowflake session
try:
    session = Session.builder.configs(connection_parameters).create()
except Exception as e:
    st.error(f"Failed to connect to Snowflake: {e}")

# Fetch fruit options from Snowflake
def fetch_fruit_options(session):
    try:
        fruit_data = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME')).collect()
        return [row['FRUIT_NAME'] for row in fruit_data]
    except Exception as e:
        st.error(f"Error fetching fruit options: {e}")
        return []

# Insert order into Snowflake
def submit_order(session, name, ingredients):
    ingredients_str = ", ".join(ingredients)
    query = f"""
        INSERT INTO smoothies.public.orders (INGREDIENTS, name_on_order)
        VALUES ('{ingredients_str}', '{name}')
    """
    try:
        session.sql(query).collect()
        st.success("Your Smoothie order has been submitted!", icon="✅")
    except Exception as e:
        st.error(f"Failed to submit order: {e}")

# Form for smoothie customization
name_on_order = st.text_input("Name on Smoothie:")
ingredients = st.multiselect("Choose up to 5 ingredients:", fetch_fruit_options(session), max_selections=5)

if st.button("Submit Order"):
    if name_on_order and ingredients:
        submit_order(session, name_on_order, ingredients)
    else:
        st.warning("Please enter your name and select at least one ingredient.")

# Call the Fruityvice API to get data about a specific fruit
fruityvice_response = requests.get("https://fruityvice.com/api/fruit/watermelon")

# Check if the response was successful
if fruityvice_response.status_code == 200:
    # Extract JSON data from the response
    fruityvice_data = fruityvice_response.json()
    
    # Display the JSON data as text
    st.text("Raw JSON data from Fruityvice API:")
    st.json(fruityvice_data)  # Display JSON data in Streamlit

    # Convert JSON data into a pandas DataFrame and display it
    import pandas as pd
    fv_df = pd.DataFrame([fruityvice_data])
    st.write("Fruityvice Dataframe:")
    st.dataframe(fv_df)  # Display as a DataFrame
else:
    # If the request was unsuccessful, show an error message
    st.error(f"Failed to retrieve data from Fruityvice API. Status code: {fruityvice_response.status_code}")

# Import necessary libraries
import streamlit as st
import pandas as pd  # Pandas for data handling
import requests  # Requests for API calls
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

# Fetch fruit options from Snowflake, including the new 'SEARCH_ON' column
def fetch_fruit_options(session):
    try:
        fruit_data = session.table("smoothies.public.fruit_options").select(
            col('FRUIT_NAME'), col('SEARCH_ON')
        ).collect()
        return pd.DataFrame(fruit_data)
    except Exception as e:
        st.error(f"Error fetching fruit options: {e}")
        return pd.DataFrame()

# Fetch the fruit options as a Pandas DataFrame
pd_df = fetch_fruit_options(session)

# Create multiselect for ingredients with values from the 'FRUIT_NAME' column
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=pd_df["FRUIT_NAME"],
    max_selections=5
)

# Display the nutritional info for each selected fruit using Fruityvice API
if ingredients_list:
    for fruit_chosen in ingredients_list:
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f"The search value for {fruit_chosen} is {search_on}.")
        
        # Get nutritional information from Fruityvice API
        try:
            fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on}")
            if fruityvice_response.status_code == 200:
                fruityvice_data = fruityvice_response.json()
                # Convert to DataFrame and display
                fv_df = pd.DataFrame([fruityvice_data])
                st.subheader(f"{fruit_chosen} Nutrition Information")
                st.dataframe(fv_df)
            else:
                st.warning(f"No data found for {fruit_chosen}")
        except Exception as e:
            st.error(f"Failed to fetch data for {fruit_chosen}: {e}")

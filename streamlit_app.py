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

# Fetch fruit options from Snowflake, including the 'SEARCH_ON' column
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

# Input for the name on the smoothie
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Create multiselect for ingredients with values from the 'FRUIT_NAME' column
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=pd_df["FRUIT_NAME"],
    max_selections=5
)

# Display the nutritional info for each selected fruit using Fruityvice API
if ingredients_list:
    ingredients_string = ', '.join(ingredients_list)
    for fruit_chosen in ingredients_list:
        # Get the corresponding search term from 'SEARCH_ON' column
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f"The search value for {fruit_chosen} is {search_on}.")
        
        # Fetch nutritional information from Fruityvice API
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

# Button to submit the smoothie order to Snowflake
if st.button("Submit Order"):
    if not name_on_order:
        st.warning("Please enter a name for your smoothie.")
    elif not ingredients_list:
        st.warning("Please select at least one ingredient.")
    else:
        # Prepare the SQL statement for inserting the order
        my_insert_stmt = f"""
            INSERT INTO smoothies.public.orders (INGREDIENTS, name_on_order)
            VALUES ('{ingredients_string}', '{name_on_order}')
        """
        try:
            # Execute the insertion query
            session.sql(my_insert_stmt).collect()
            st.success("Your Smoothie is ordered!", icon="✅")
        except Exception as e:
            st.error(f"Failed to submit order: {e}")

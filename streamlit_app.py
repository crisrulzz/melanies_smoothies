# Import necessary libraries
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col

# Set the title and description of the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Input field for smoothie name
name_on_order = st.text_input('Name on Smoothie:')
if name_on_order:
    st.write(f"The name on your Smoothie will be: **{name_on_order}**")

# Establish Snowflake session
session = get_active_session()

# Retrieve fruit options from Snowflake and convert to pandas DataFrame
try:
    my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
    pd_df = my_dataframe.to_pandas()
except Exception as e:
    st.error(f"Error fetching data from Snowflake: {e}")
    pd_df = pd.DataFrame(columns=['FRUIT_NAME', 'SEARCH_ON'])  # Empty DataFrame as fallback

# Multi-select widget for selecting ingredients
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=pd_df['FRUIT_NAME'],
    max_selections=5
)

# Display additional information for each selected ingredient
if ingredients_list:
    for fruit_chosen in ingredients_list:
        # Retrieve the search value for the selected fruit
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        # Display the search value sentence
        st.write(f"The search value for **{fruit_chosen}** is **{search_on}**.")
        
        # Display the nutrition information for the fruit
        st.subheader(f"{fruit_chosen} Nutrition Information")
        
        # Attempt to get nutrition information from API, with a default table if not found
        try:
            fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on.lower()}")
            if fruityvice_response.status_code == 200:
                # Convert response to DataFrame and display
                fruityvice_data = fruityvice_response.json()
                fv_df = pd.DataFrame([fruityvice_data])
                st.dataframe(fv_df, use_container_width=True)
            else:
                # Display "Not Found" if API response is not 200 OK
                st.table(pd.DataFrame({"Error": ["Not Found"]}))
        except Exception as e:
            # Display "Not Found" in case of an exception
            st.table(pd.DataFrame({"Error": ["Not Found"]}))

    # Join selected ingredients into a single string
    ingredients_string = ', '.join(ingredients_list)
    
    # Insert statement for placing the order
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (INGREDIENTS, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    # Button to submit the order
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        try:
            session.sql(my_insert_stmt).collect()
            st.success('Your Smoothie is ordered!', icon="✅")
        except Exception as e:
            st.error(f"Error submitting order: {e}")

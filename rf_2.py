import streamlit as st
import requests
import json
import pandas as pd

# URL of the recipe data
DATA_URL = "https://openrecipes.s3.amazonaws.com/openrecipes.txt"

@st.cache_data
def fetch_and_parse_data(url):
    response = requests.get(url)
    response.raise_for_status()
    text_data = response.text
    # The data appears to be JSON objects separated by newlines
    recipes = []
    for line in text_data.splitlines():
        if line.strip():
            try:
                recipe = json.loads(line)
                recipes.append(recipe)
            except json.JSONDecodeError:
                continue
    return recipes

def preprocess_data(recipes):
    # Convert list of dicts to DataFrame
    df = pd.json_normalize(recipes)

    # Extract some common fields for search/display
    # For example, title, description, tags, categories, ingredients
    # Handle missing data
    for col in ['name', 'description', 'tags', 'categories', 'ingredients']:
        if col not in df.columns:
            df[col] = ''

    return df

def main():
    st.title("Recipe Rolodex")
    loading_box = st.empty()
    loading_box.write("Fetching and processing recipe data...")

    recipes = fetch_and_parse_data(DATA_URL)
    df = preprocess_data(recipes)

    loading_box.write("Now ready to serve!!")

    # Combine some text fields for better search
    df['search_text'] = (
        df['name'].astype(str) + ' ' +
        df['description'].astype(str) + ' ' +
        df['tags'].astype(str) + ' ' +
        df['categories'].astype(str) + ' ' +
        df['ingredients'].astype(str)
    ).str.lower()

    # Sidebar filters
    st.sidebar.header("Filters")
    categories = sorted(set(df['categories'].dropna().str.cat(sep='|').split('|')))
    selected_category = st.sidebar.selectbox("Category", ['All'] + categories)

    tags = sorted(set(df['tags'].dropna().str.cat(sep='|').split('|')))
    selected_tag = st.sidebar.selectbox("Tag", ['All'] + tags)

    # Search box
    query = st.text_input("Search recipes:")

    # Filter based on selections
    filtered_df = df
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['categories'].str.contains(selected_category, case=False, na=False)]
    if selected_tag != 'All':
        filtered_df = filtered_df[filtered_df['tags'].str.contains(selected_tag, case=False, na=False)]
    if query:
        filtered_df = filtered_df[filtered_df['search_text'].str.contains(query.lower())]

    # Display results
    if not filtered_df.empty:
        selected_recipe_idx = st.selectbox("Select a recipe:", filtered_df.index)
        recipe = filtered_df.loc[selected_recipe_idx]
        st.subheader(recipe['name'])
        st.write(f"**Description:** {recipe['description']}")
        st.write(f"**Ingredients:** {recipe['ingredients']}")
        st.write(f"**Tags:** {recipe['tags']}")
        st.write(f"**Categories:** {recipe['categories']}")
        st.write(f"**Instructions:** {recipe.get('instructions', 'No instructions provided.')}")
    else:
        st.write("No recipes found matching your criteria.")

if __name__ == "__main__":
    main()


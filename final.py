import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.markdown("# Hoya 1 - Capstone")

# Load the Crime Statistics CSV file
crimerate_df = pd.read_csv("crimerate.csv")

# Load the Age Population Distribution data
years = [2016, 2017, 2018, 2019, 2020]
dfs = []
for year in years:
    file_path = f"popdist{year}.csv"
    df = pd.read_csv(file_path, skiprows=2).drop(columns=['Footnotes'], errors='ignore')
    df['Year'] = year
    dfs.append(df)
combined_df = pd.concat(dfs, axis=0, ignore_index=True)

# Dataset Selection
datasets = ["Crime Statistics", "Age Population Distribution"]
selected_dataset = st.selectbox("Select a dataset:", datasets)

if selected_dataset == "Crime Statistics":
    # State Selector for Crime Statistics
    state_selected = st.selectbox("Select a state:", crimerate_df['state'].unique())
    state_data = crimerate_df[crimerate_df['state'] == state_selected].iloc[0]

    st.markdown(f"## Crime Statistics for {state_selected}")

    # National Averages
    national_avg_pop = crimerate_df['pop2020'].mean()
    national_avg_reported = crimerate_df['reported'].mean()
    national_avg_rate = crimerate_df['rate'].mean()

    # Helper function for percentage difference
    def compare_to_national(state_value, national_value):
        percentage_diff = ((state_value - national_value) / national_value) * 100
        if percentage_diff > 0:
            return f"↑ national avg by {percentage_diff:.2f}%"
        else:
            return f"↓ national avg by {abs(percentage_diff):.2f}%"

    # Displaying the data with comparisons using columns
    col1, col2, col3 = st.columns(3)

# Displaying Population Data
    col1.write(f"Population (2020): {state_data['pop2020']:,}")
    col2.write(f"National Average: {national_avg_pop:,.0f}")
    col3.write(f"{compare_to_national(state_data['pop2020'], national_avg_pop)}")

# Displaying Total Reported Crimes Data
    col1.write(f"Total Reported Crimes: {state_data['reported']:,}")
    col2.write(f"National Average: {national_avg_reported:,.0f}")
    col3.write(f"{compare_to_national(state_data['reported'], national_avg_reported)}")

# Displaying Crime Rate Data
    col1.write(f"Crime Rate: {round(state_data['rate']):,} per 100,000 people")
    col2.write(f"National Average: {round(national_avg_rate):,.0f}")
    col3.write(f"{compare_to_national(state_data['rate'], national_avg_rate)}")

    # Crime Visualization
    labels = [f'Violent Crimes ({state_data["violent"]:,})', f'Non-Violent Crimes ({state_data["nonViolent"]:,})']
    values = [state_data['violent'], state_data['nonViolent']]
    fig, ax = plt.subplots()
    ax.bar(labels, values, color=['red', 'blue'])
    ax.set_ylabel('Number of Crimes')
    ax.set_title('Violent vs. Non-Violent Crimes')
    st.pyplot(fig)

elif selected_dataset == "Age Population Distribution":
    # State Selector for Age Population Distribution
    state_selected = st.selectbox("Select a state:", combined_df['Location'].unique())
    state_data = combined_df[combined_df['Location'] == state_selected]

    # Age Population Distribution Visualization
    plt.figure(figsize=(15,8))
    for column in state_data.columns[1:-2]:
        plt.plot(state_data['Year'], state_data[column]/1000, label=column)  # Divide by 1,000

    plt.title(f"Age Population Distribution for {state_selected} over Time")
    plt.xlabel("Year")
    plt.ylabel("Population in Thousands")  # Updated y-axis label

    # Move the legend to the right side
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # Ensure the x-axis only displays whole years
    plt.xticks(state_data['Year'].unique().astype(int))

    # Adjust y-ticks format
    ax = plt.gca()
    ax.get_yaxis().get_major_formatter().set_scientific(False)

    plt.grid(True)
    st.pyplot(plt)
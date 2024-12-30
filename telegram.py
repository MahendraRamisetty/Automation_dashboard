import pandas as pd
import panel as pn
import matplotlib.pyplot as plt
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from matplotlib.backends.backend_pdf import PdfPages
import io
from datetime import datetime
import plotly.express as px
import pandas as pd


def  calculate_telegram_summary(data):
    total_properties_telegram = data['propertyname'].nunique()
    total_fixture_telegarm = data['fixtures'].nunique()
    total_infringements_telegram = data['URL'].nunique()
    total_telegramChannel_names = data['DomainName'].nunique()
    approved_removed_filter = data[data['Status'].isin(['Approved', 'Removed'])]['URL'].nunique()
    removal_percentage = (approved_removed_filter / total_infringements_telegram) * 100 if total_infringements_telegram > 0 else 0
    #data['views'] = data['views'].str.replace(',', '')
    views_incurred = pd.to_numeric(data['views'], errors='coerce').sum()
    print(views_incurred)
    no_of_channels_suspended = data[data['ChannelStatus'].isin(['Suspended'])]['URL'].nunique()
    print(no_of_channels_suspended)
    Total_subcribers = pd.to_numeric(data['channelsubscribers'], errors='coerce').sum()
    impacted_subcribers = pd.to_numeric(data[data['Status'].isin(['Approved', 'Removed'])]['channelsubscribers'], errors='coerce').sum()
  

    return impacted_subcribers, Total_subcribers, no_of_channels_suspended, total_fixture_telegarm, total_infringements_telegram, total_properties_telegram, total_telegramChannel_names, removal_percentage, views_incurred
    

# Function to get top 5 property's based on total URLs
def get_top_telegram_property(data):
    telgramproperty_summary= data.groupby(['propertyname', 'URL']).agg(
        removal_flag=('Status', lambda x: any(x.isin(['Approved', 'Removed'])))
    ).reset_index()

    telgramproperty_summary = telgramproperty_summary.groupby('propertyname').agg(
        total_urls=('URL', 'count'),
        removal_count=('removal_flag', 'sum')
    ).reset_index().sort_values(by='total_urls', ascending=False)

    return telgramproperty_summary.nlargest(5, 'total_urls')[['propertyname', 'total_urls', 'removal_count']]



#fucntio to get telegram summary
def get_telegram_platform_data(data):

    platform = data[data['SheetName'] == 'Telegram']
    # Calculate total URLs, count of 'Removed' and 'Approved' statuses for each DomainName
    Telegram_summary = platform.groupby('DomainName').agg(
        total_urls=('URL', 'count'),
        removed_count=('Status', lambda x: x.isin(['Approved', 'Removed']).sum()),
    ).reset_index().sort_values(by='total_urls', ascending=False)
    
    return Telegram_summary


#telegram wigents styled as card

def widgets():
    # Standard properties
    card_width = 150
    card_height = 150  # Fixed height for uniformity
    card_margin = (5, 5)
    card_font_size = "20pt"

    # Cards with consistent height and custom CSS class
    total_properties_telegram_card = pn.Card(
        pn.indicators.Number(value=0, format="{value}", font_size=card_font_size),
        title="Total Properties", width=card_width, height=card_height, margin=card_margin
    )

    total_fixture_telegram_card = pn.Card(
        pn.indicators.Number(value=0, format="{value}", font_size=card_font_size),
        title="Total Fixtures", width=card_width, height=card_height, margin=card_margin
    )

    total_infringements_telegram_card = pn.Card(
        pn.indicators.Number(value=0, format="{value}", font_size=card_font_size),
        title="Total Infringements", width=card_width, height=card_height, margin=card_margin
    )

    number_of_websites_telegram_card = pn.Card(
        pn.indicators.Number(value=0, format="{value}", font_size=card_font_size),
        title="Total Channel", width=card_width, height=card_height, margin=card_margin
    )

    removal_percentage_telegram_card = pn.Card(
        pn.indicators.Number(value=0, format="{value:.2f}%", font_size=card_font_size),
        title="% Removal", width=card_width, height=card_height, margin=card_margin
    )

    views_incurred_card = pn.Card(
        pn.indicators.Number(value=0, format="{value}", font_size=card_font_size),
        title="Total Views", width=card_width, height=card_height, margin=card_margin
    )

    no_of_channels_suspended_card = pn.Card(
        pn.indicators.Number(value=0, format="{value}", font_size=card_font_size),
        title="Channels Suspended", width=card_width, height=card_height, margin=card_margin
    )

    total_subscribers_card = pn.Card(
        pn.indicators.Number(value=0, format="{value}", font_size=card_font_size),
        title="Total Subscribers", width=card_width, height=card_height, margin=card_margin
    )

    impacted_subscribers_card = pn.Card(
        pn.indicators.Number(value=0, format="{value}", font_size=card_font_size),
        title="Impacted Subscribers", width=card_width, height=card_height, margin=card_margin
    )
      
    # Arrange cards in a Row layout
    dashboard = pn.Row(
        total_properties_telegram_card, total_fixture_telegram_card, total_infringements_telegram_card,
        number_of_websites_telegram_card, removal_percentage_telegram_card, views_incurred_card,
        no_of_channels_suspended_card, total_subscribers_card, impacted_subscribers_card
    )

    # Return individual widgets and the dashboard layout
    return (total_properties_telegram_card, total_fixture_telegram_card, total_infringements_telegram_card,
            number_of_websites_telegram_card, removal_percentage_telegram_card, views_incurred_card,
            no_of_channels_suspended_card, total_subscribers_card, impacted_subscribers_card, dashboard)


# Function to get top 5 fixtures based on total URLs in the "Telegram" sheet
def get_telegram_top_fixtures(data):
    # Filter data for the "Telegram" sheet only
    telegram_data = data[data['SheetName'] == 'Telegram']
    
    # Group by 'fixtures' and 'URL', calculate removal flag
    fixture_summary = telegram_data.groupby(['fixtures', 'URL']).agg(
        removal_flag=('Status', lambda x: any(x.isin(['Approved', 'Removed'])))
    ).reset_index()

    # Aggregate by 'fixtures' to count total URLs and removal count
    fixture_summary = fixture_summary.groupby('fixtures').agg(
        total_urls=('URL', 'count')
    ).reset_index().sort_values(by='total_urls', ascending=False)

    # Select top 5 fixtures based on total URLs
    return fixture_summary.nlargest(5, 'total_urls')[['fixtures', 'total_urls']]

# Function to create a grouped bar chart for the top 5 fixtures in the "Telegram" sheet
def create_telegram_top_fixtures_bar_chart(top_fixtures):
    # Sort data for better presentation in the horizontal chart
    top_fixtures = top_fixtures.sort_values(by='total_urls', ascending=True)
    max_value = top_fixtures['total_urls'].max()
    buffer = max_value * 0.2  # 20% buffer for extended x-axis
    x_axis_limit = max_value + buffer
    
    # Create the plot with Plotly Express
    fig = px.bar(
        top_fixtures,
        y='fixtures',  # Fixtures as the labels on the y-axis
        x='total_urls',  # Total URLs on the x-axis
        orientation='h',  # Horizontal bar chart
        title="Top 5 Telegram Channels – Basis No. of Infringements",
        text='total_urls',  # Display count at the end of each bar
    )
    
    # Customize the chart
    fig.update_traces(marker_color='#4a90e2', textposition='outside')  # Set color to blue and position text outside the bar
    fig.update_layout(
        plot_bgcolor='#f9f9f9',  # Light gray background color
        xaxis=dict(
            gridcolor='rgba(0, 0, 0, 0.2)',  # Dotted grid lines for x-axis
            gridwidth=1,
            showline=False,
            range=[0, x_axis_limit]  # Use extended x-axis limit
        ),
        yaxis=dict(
            title=None,  # Remove y-axis title
            categoryorder='total ascending'  # Ensure the bars are sorted properly
        ),
        title=dict(
            font=dict(size=18, color='#333'),
            x=0.5,  # Center the title
            xanchor='center'
        ),
        margin=dict(l=100, r=40, t=80, b=40),  # Adjust margins
         # Slightly increase figure height
    )
    # Add interactivity: hover tooltip showing fixture name and total URLs count
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Total URLs: %{x}<extra></extra>"
    )

    return fig


def telegram_domains_by_subscribers(data, selected_fixture=None):
    # Filter data for the "Telegram" sheet
    telegram_data = data[data['SheetName'] == 'Telegram']
    
    # Apply fixture filtering if a specific fixture is selected
    if selected_fixture:
        telegram_data = telegram_data[telegram_data['fixtures'] == selected_fixture]
    
    # Convert 'channelsubscribers' to numeric, forcing errors to NaN
    telegram_data['channelsubscribers'] = pd.to_numeric(telegram_data['channelsubscribers'], errors='coerce')
    
    # Fill NaN values with 0
    telegram_data['channelsubscribers'].fillna(0, inplace=True)
    
    # Group by 'DomainName' and sum the 'channelsubscribers'
    domain_summary = telegram_data.groupby('DomainName').agg(
        total_subscribers=('channelsubscribers', 'sum')
    ).reset_index()
    
    # Sort by total subscribers and select the top 10
    top_10_domains = domain_summary.nlargest(10, 'total_subscribers')
    
    return top_10_domains



def create_treemap_chart_telegram(top_10_data):
    fig = px.treemap(
        top_10_data,
        path=['DomainName'],  # Use 'DomainName' as the label for each rectangle
        values='total_subscribers',  # Size of each rectangle is based on total subscribers
        title="Top 10 Telegram Channels - Based on Subscribers",
    )
    
    # Customize the chart with a vibrant color scale
    fig.update_traces(
        marker=dict(colorscale='Viridis'),
        textinfo='label+value',  # Use a vibrant colorscale and display value with label
    )
    
    # Adjust layout for improved appearance
    fig.update_layout(
    margin=dict(l=50, r=50, t=70, b=50),
    title=dict(font=dict(size=24), x=0.5, xanchor='center'),
    height=450  # Match this to the Matplotlib chart height
    )
    
    return fig


## trends grapgh for both sumamry and telgram 


def aggregate_matchday_data(data):

    """
    Aggregates data to calculate total URLs and sorts Matchday properly
    in ascending numerical order (e.g., Matchday 1, Matchday 2, ..., Matchday 11).

    """

    # Normalize Matchday column
    data['Matchday'] = data['Matchday'].str.strip().str.title()  # Remove extra spaces, normalize capitalization

    # Aggregate data
    matchday_summary = data.groupby('Matchday').agg(
        total_urls=('URL', 'count')
    ).reset_index()

    # Extract numerical part from Matchday and sort by it
    
    matchday_summary['Matchday_num'] = matchday_summary['Matchday'].str.extract(r'(\d+)$').astype(int)
    matchday_summary = matchday_summary.sort_values(by='Matchday_num', ascending=True)  # Sort in ascending order

    # Drop the temporary Matchday_num column
    matchday_summary = matchday_summary.drop(columns='Matchday_num')

    # Reset index after sorting to ensure correct indexing
    matchday_summary = matchday_summary.reset_index(drop=True)

    print(matchday_summary)

    return matchday_summary




def create_enhanced_matchday_line_plot(matchday_data):
     
    # Ensure 'Matchday' is sorted in ascending numeric order
    matchday_data['Matchday_num'] = matchday_data['Matchday'].str.extract(r'(\d+)$').astype(int)
    matchday_data = matchday_data.sort_values(by='Matchday_num', ascending=True).drop(columns='Matchday_num')

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f9f9f9')

    # Plot lines with markers
    ax.plot(matchday_data['Matchday'], matchday_data['total_urls'], marker='o', markersize=8,
            color='#ff6b6b', linewidth=2.5, label='Total URLs')

    # Annotate data points outside the graph
    for i, row in matchday_data.iterrows():
        # Position the labels outside the graph layout
        ax.annotate(f"{int(row['total_urls'])}",
                    xy=(i, row['total_urls']),  # Data point position
                    xytext=(0, 15),  # Offset (x=0, y=15)
                    textcoords='offset points',
                    ha='center', fontsize=9, color='#4a90e2', fontweight='bold')

    # Title and labels
    ax.set_title("Matchday Identification and Removal Trends", fontsize=14, fontweight='bold', pad=20)


    # Customize x-ticks and rotate labels
    ax.set_xticks(range(len(matchday_data['Matchday'])))
    ax.set_xticklabels(matchday_data['Matchday'], rotation=45, ha='right', fontsize=10)

    # Adjust y-limits to add padding above the highest value
    max_y_value = matchday_data['total_urls'].max()
    ax.set_ylim(0, max_y_value * 1.2)  # Add 20% padding above the highest value

    # Grid and background styling
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_facecolor('#f0f7ff')

    # Legend
    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))

    # Ensure the layout is adjusted to accommodate the labels
    plt.tight_layout()
    return fig



#mothly grapgh for telegram page 
#Function to get monthly totals

def telegram_monthly_totals(data):
    # Filter data for the specified sheet
    telegram_data = data[data['SheetName'] == 'Telegram']  # Adjust 'Sheet Name' to your actual column name
    
    # Ensure 'Identification Timestamp' is in datetime format
    telegram_data['Identification Timestamp'] = pd.to_datetime(telegram_data['Identification Timestamp'])
    
    # Extract the month from the timestamp
    telegram_data['Month'] = telegram_data['Identification Timestamp'].dt.to_period('M')
    
    # Group and aggregate the data
    monthly_summary = telegram_data.groupby('Month').agg(
        total_urls=('URL', 'count'),
        removal_count=('Status', lambda x: x.isin(['Approved', 'Removed']).sum())
    ).reset_index().sort_values(by='total_urls', ascending=False)
    
    # Convert 'Month' back to a timestamp
    monthly_summary['Month'] = monthly_summary['Month'].dt.to_timestamp()
    
    return monthly_summary


def telegram_monthly_totals_line_plot(monthly_data):
    # Convert 'Month' column to datetime if it's not already
    monthly_data['Month'] = pd.to_datetime(monthly_data['Month'])

    # Group data by month and sum total URLs and removal counts
    monthly_data = monthly_data.resample('M', on='Month').sum()
    monthly_data.index = monthly_data.index.strftime('%b %Y')  # Format to show "Month Year"

    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f9f9f9')

    # Plotting total URLs and removal counts with enhancements
    ax.plot(monthly_data.index, monthly_data['total_urls'], marker='o', color='#ff6b6b', linewidth=2.5,
            markersize=8, label='Total URLs')
    ax.plot(monthly_data.index, monthly_data['removal_count'], marker='D', color='#4a90e2', linewidth=2.5,
            markersize=8, label='Removal Count')

    # Adjust y-limits to add padding above the highest value
    max_y_value = max(monthly_data['total_urls'].max(), monthly_data['removal_count'].max())
    ax.set_ylim(0, max_y_value * 1.2)  # Add 20% padding above the highest value

    # Add data point labels with adjusted positions and styling for readability
    for i, (month, row) in enumerate(monthly_data.iterrows()):
        ax.annotate(f"{int(row['total_urls'])}",
                    xy=(i, row['total_urls']),  # Data point position
                    xytext=(0, 10),  # Offset (x=0, y=10)
                    textcoords='offset points',
                    ha='center', fontsize=9, color='#ff6b6b', fontweight='bold')
        ax.annotate(f"{int(row['removal_count'])}",
                    xy=(i, row['removal_count']),  # Data point position
                    xytext=(0, 10),  # Offset (x=0, y=10)
                    textcoords='offset points',
                    ha='center', fontsize=9, color='#4a90e2', fontweight='bold')

    # Enhanced title and axis labels
    ax.set_title("Overall piracy Identification and Removal", fontsize=10, fontweight='bold', pad=20)
    ax.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')

    # Set custom x-tick labels to show every month and rotate for clarity
    ax.set_xticks(range(len(monthly_data.index)))
    ax.set_xticklabels(monthly_data.index, rotation=45, ha='right', fontsize=10)

    # Add gridlines and background gradient for a cleaner look
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_facecolor('#f0f7ff')  # Light background color for the plot area

    # Add legend with updated font size
    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))

    # Ensure the layout is adjusted to accommodate the labels
    plt.tight_layout()
    return fig




# Function to get top 5 fixtures based on summed "views" in the "Telegram" sheet
def top_fixtures_donut_chart(data):
    # Filter data for the "Telegram" sheet only
    telegram_data = data[data['SheetName'] == 'Telegram']
    
    # Convert "views" column to numeric and drop invalid rows
    telegram_data['views'] = pd.to_numeric(telegram_data['views'], errors='coerce')
    telegram_data = telegram_data.dropna(subset=['views'])
    
    # Group by 'fixtures' and sum the 'views'
    fixture_summary = telegram_data.groupby('fixtures', as_index=False)['views'].sum()
    
    # Sort fixtures by summed "views" in descending order
    fixture_summary = fixture_summary.sort_values(by='views', ascending=False)
    
    # Select top 5 fixtures
    return fixture_summary.nlargest(5, 'views')[['fixtures', 'views']]


# Function to create a donut chart for the top 5 fixtures based on views
def top_fixtures_graph_donut_chart(top_fixtures):
    # Sort data by views in descending order (optional for visual consistency)
    top_fixtures = top_fixtures.sort_values(by='views', ascending=False)
    
    # Create the donut chart
    fig = px.pie(
        top_fixtures,
        names='fixtures',  # Labels for the chart
        values='views',  # Values to determine the size of the slices
        title="Top 5 Fixtures – Based on Views",
        hole=0.4,  # Creates a donut chart
    )
    
    # Customize the chart
    fig.update_traces(
        textinfo='label+percent',  # Display label and percentage on slices
        marker=dict(line=dict(color='#000000', width=2)),  # Black border for better contrast
    )
    
    fig.update_layout(
        title=dict(
            text="Top 5 fixtures – Basis Number of Views",
            font=dict(size=18, color='#333'),
            x=0.5,  # Center the title
            xanchor='center'
        ),
        margin=dict(l=40, r=150, t=80, b=40),  # Adjust margins to make space for the legend
        plot_bgcolor='#f9f9f9',  # Light gray background color
    )
    
    return fig


def create_channel_type_pie_chart(data):
    # Filter data for the "Telegram" sheet only
    telegram_data = data[data['SheetName'] == 'Telegram']
    
    # Retain only valid values in the "channeltype" column (e.g., "Public" or "Private")
    valid_channel_types = ['Public', 'Private']
    filtered_data = telegram_data[telegram_data['ChannelType'].isin(valid_channel_types)]
    
    # Group by 'channeltype' and count occurrences
    channeltype_summary = filtered_data['ChannelType'].value_counts().reset_index()
    channeltype_summary.columns = ['ChannelType', 'count']

    # Create the pie chart
    fig = px.pie(
        channeltype_summary,
        names='ChannelType',  # Values for the pie slices
        values='count',  # Size of each slice
        title="Telegram Channel - Type of Channel",
        hole=0.4,  # Donut chart style
    )
    
    # Customize the chart
    fig.update_traces(
        textinfo='label+percent',  # Display label and percentage
        marker=dict(line=dict(color='#000000', width=1.5))  # Add borders around slices
    )
    
    fig.update_layout(
        title=dict(
            text="Telegram Channel - Type of Channel",
            font=dict(size=18, color='#333'),
            x=0.5,  # Center the title
            xanchor='center'
        ),
        legend=dict(
            orientation="v",  # Vertical legend
            y=0.5,
            x=1.1,  # Place legend on the right side
            title="ChannelType",
        ),
        margin=dict(l=40, r=40, t=80, b=40),  # Adjust margins for spacing
        plot_bgcolor='#f9f9f9',  # Light gray background color
    )

    return fig


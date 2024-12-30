import pandas as pd
import plotly.express as px
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure 
from PIL import ImageFont
from PIL import Image
import plotly.graph_objects as go
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image, ImageDraw, ImageFont
import io
import panel as pn
import matplotlib.pyplot as plt
import numpy as np



# Summary metric calculation function
def calculate_summary(data):
    total_properties = data['propertyname'].nunique()
    total_fixture = data['fixtures'].nunique()
    number_of_websites = data['DomainName'].nunique()
    total_infringements = data['URL'].nunique()
    approved_removed_filter = data[data['Status'].isin(['Approved', 'Removed'])]['URL'].nunique()
    removal_percentage = (approved_removed_filter / total_infringements) * 100 if total_infringements > 0 else 0
    return total_properties, total_fixture, total_infringements, number_of_websites, removal_percentage


# Function to create a grouped bar chart for the top 5 property
def create_top_property_bar_chart(top_fixtures):
    fig, ax = plt.subplots(figsize=(8, 5), facecolor='#f2f2f2')
    x = np.arange(len(top_fixtures['propertyname']))
    bar_width = 0.3

    bar1 = ax.bar(x - bar_width / 2, top_fixtures['total_urls'], width=bar_width, label='Total URLs', color='#ff6b6b')
    bar2 = ax.bar(x + bar_width / 2, top_fixtures['removal_count'], width=bar_width, label='Removal Count', color='#4a90e2')

    ax.set_title("Top 5 properties Identification and Removal", fontsize=12, fontweight='bold', pad=20)
    ax.set_ylim(0, max(top_fixtures['total_urls'].max(), top_fixtures['removal_count'].max()) * 1.15)
    ax.set_ylabel('Value', fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(top_fixtures['propertyname'], rotation=45, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper right')
    
    for bar in bar1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10, int(bar.get_height()), ha='center', va='bottom', fontsize=8)
    for bar in bar2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10, int(bar.get_height()), ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    return fig



# Function to get top 5 fixtures based on total URLs
def get_top_fixtures(data):
    fixture_summary = data.groupby(['fixtures', 'URL']).agg(
        removal_flag=('Status', lambda x: any(x.isin(['Approved', 'Removed'])))
    ).reset_index()

    fixture_summary = fixture_summary.groupby('fixtures').agg(
        total_urls=('URL', 'count'),
        removal_count=('removal_flag', 'sum')
    ).reset_index().sort_values(by='total_urls', ascending=False)

    return fixture_summary.nlargest(5, 'total_urls')[['fixtures', 'total_urls', 'removal_count']]

# Function to create a grouped bar chart for the top 5 fixtures
def create_top_fixtures_bar_chart(top_fixtures):
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f8f9fa')  # Light background
    x = np.arange(len(top_fixtures['fixtures']))
    bar_width = 0.3

    # Improved bar colors
    bar1 = ax.bar(x - bar_width / 2, top_fixtures['total_urls'], width=bar_width, label='Total URLs', color='#ff6b6b', edgecolor='black', linewidth=0.7)
    bar2 = ax.bar(x + bar_width / 2, top_fixtures['removal_count'], width=bar_width, label='Removal Count', color='#4a90e2', edgecolor='black', linewidth=0.7)

    # Enhanced title and labels                                      #4a90e2
    ax.set_title("Top 5 Fixtures — Identification and Removal", fontsize=14, fontweight='bold', pad=20, loc='center')
    ax.set_xlabel('')  # If you don’t want a label, provide an empty string
    ax.set_ylabel('Count', fontsize=12, fontweight='bold', labelpad=10)

    # Customizing the x-axis ticks
    ax.set_xticks(x)
    ax.set_xticklabels(top_fixtures['fixtures'], rotation=45, ha='right', fontsize=10)

    # Adjusting grid and background
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_facecolor('#f5f5f5')  # Light gray background inside the plot area
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Adding annotations
    for bar in bar1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02 * max(top_fixtures['total_urls']), 
                f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='#ff6b6b')
    for bar in bar2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02 * max(top_fixtures['removal_count']), 
                f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='#4a90e2')

    # Legend customization
    ax.legend(loc='upper right', fontsize=10, facecolor='white', edgecolor='black')

    plt.tight_layout()
    return fig


# Function to create platform-wise bar chart

def create_bar_chart(data, propertyname="All Properties", fixture="All Fixtures", max_fixtures_display=3):
   # Group and aggregate data
    sheet_summary = data.groupby('SheetName').agg(
        total_urls=('URL', 'nunique'),
        removal_percentage=('Status', lambda x: x.isin(['Approved', 'Removed']).sum())
    ).reset_index().sort_values(by='total_urls', ascending=False)

    # Handle long fixture lists for the title with line wrapping
    if isinstance(fixture, list):
        if len(fixture) > max_fixtures_display:
            fixture_display = ", ".join(fixture[:max_fixtures_display]) + "..."
        else:
            fixture_display = ", ".join(fixture)
    else:
        fixture_display = fixture

    # Add line breaks for long titles
    dynamic_title = f"Sheet wise identification & Delisted for {propertyname}\nFixtures: {fixture_display}"
    
    # Plot setup
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f2f2f2')
    x = np.arange(len(sheet_summary['SheetName']))
    bar_width = 0.3

    # Bars for total URLs and removal count
    bar1 = ax.bar(x - bar_width / 2, sheet_summary['total_urls'], width=bar_width, color='#ff6b6b', label='Total URLs')
    bar2 = ax.bar(x + bar_width / 2, sheet_summary['removal_percentage'], width=bar_width, color='#4a90e2', label='Removal Count')
    
    # Set a wrapped title with line break
    ax.set_title(dynamic_title, fontsize=12, fontweight='bold', pad=30, loc='center', wrap=True)
    ax.set_yscale('log')  # Setting the y-axis to logarithmic scale
    
    # Adjust Y-axis limits to prevent overlap at top and bottom
    min_ylim = 1 if sheet_summary['removal_percentage'].min() > 0 else 0.5
    max_ylim = ax.get_ylim()[1] * 1.3  # Increased space above the highest bar
    ax.set_ylim(min_ylim, max_ylim)

    # Annotations for bars with dynamic positioning
    for bar in bar1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + (0.15 * height if height > 0 else 0.5), 
                f'{int(height)}', ha='center', va='bottom', fontsize=8)

    for bar in bar2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + (0.15 * height if height > 0 else 0.5), 
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
        
    # Axis and legend settings
    ax.set_facecolor('#e6e6e6')
    ax.set_ylabel('Value (log scale)', fontsize=10, fontweight='bold')  # Indicating log scale on the label
    ax.set_xticks(x)
    ax.set_xticklabels(sheet_summary['SheetName'], rotation=30, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Remove xlabel (x-axis label is not needed)
    ax.set_xlabel(None)

    # Adjust legend position to prevent overlap with the chart
    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))
    
    plt.tight_layout()
    return fig
    
# Function to get monthly totals
def get_monthly_totals(data):
    data['Month'] = data['Identification Timestamp'].dt.to_period('M')
    monthly_summary = data.groupby('Month').agg(
        total_urls=('URL', 'count'),
        removal_count=('Status', lambda x: x.isin(['Approved', 'Removed']).sum())
    ).reset_index().sort_values(by='total_urls', ascending=False)
    monthly_summary['Month'] = monthly_summary['Month'].dt.to_timestamp()
    return monthly_summary

def create_monthly_totals_line_plot(monthly_data):
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
    ax.set_title("Monthly Identification and Removal Trends", fontsize=14, fontweight='bold', pad=20)
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

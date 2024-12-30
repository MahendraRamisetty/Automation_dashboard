
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






# Function to get domain-specific data for SocialMediaPlatforms
def get_social_media_platform_data(data):
    # Filter data for SocialMediaPlatforms sheet
    social_media_data = data[data['SheetName'] == 'SocialMediaPlatforms']

    # Calculate total URLs, count of 'Removed' and 'Approved' statuses for each DomainName
    domain_summary = social_media_data.groupby('DomainName').agg(
        total_urls=('URL', 'count'),
        removed_count=('Status', lambda x: x.isin(['Approved', 'Removed']).sum()),
    ).reset_index().sort_values(by='total_urls', ascending=False)
    
    return domain_summary

# Function to create a grouped bar chart for SocialMediaPlatforms
def create_social_media_platform_bar_chart(domain_data):
    # Set up figure and axis
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f8f9fa')
    x = np.arange(len(domain_data['DomainName']))
    bar_width = 0.3  # Adjust bar width to increase spacing

    # Plotting each metric
    bar1 = ax.bar(x - bar_width / 2, domain_data['total_urls'], width=bar_width, label='Total URLs', color='#ff6b6b')
    bar2 = ax.bar(x + bar_width / 2, domain_data['removed_count'], width=bar_width, label='Delisting Count', color='#4a90e2')

    # Calculate highlights
    total_feeds_removed = (domain_data['removed_count'].sum() / domain_data['total_urls'].sum()) * 100
    top_platform = domain_data.loc[domain_data['removed_count'].idxmax()]

    # Title with highlights included
    highlight_text = (
        f"Highlights:\n"
        f"• {total_feeds_removed:.1f}% of pirate feeds removed\n"
        f"• Top Platform: {top_platform['DomainName']} ({top_platform['removed_count']}/{top_platform['total_urls']}) removed"
    )

    title_text = f"Platform-wise Analysis for Social Media\n{highlight_text}"
    ax.set_title(title_text, fontsize=14, fontweight='bold', pad=30, loc='center')
    ax.set_xlabel('')  # If you don’t want a label, provide an empty string

    # Y-axis setup
    ax.set_ylabel('Count (Log Scale)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_yscale('log')  # Applying logarithmic scale to y-axis
    max_value = max(domain_data['total_urls'].max(), domain_data['removed_count'].max())
    ax.set_ylim(1, max_value * 2)  # Add 100% padding above the highest value for much more height

    # X-axis setup
    ax.set_xticks(x)
    ax.set_xticklabels(domain_data['DomainName'], rotation=30, ha='right', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Add bar labels for better visibility
    for bar in bar1:
        height = bar.get_height()
        offset = 1.2  # Constant small offset for better positioning
        ax.text(
            bar.get_x() + bar.get_width() / 2, 
            height + offset,  # Offset value adjusted for log scale
            f'{int(height)}', 
            ha='center', 
            va='bottom', 
            fontsize=10, 
            color='#ff6b6b'
        )

    for bar in bar2:
        height = bar.get_height()
        offset = 1.2  # Same constant offset for the second group
        ax.text(
            bar.get_x() + bar.get_width() / 2, 
            height + offset,  # Offset value adjusted for log scale
            f'{int(height)}', 
            ha='center', 
            va='bottom', 
            fontsize=10, 
            color='#4a90e2'
        )

    ax.legend(loc='upper right', fontsize=10, facecolor='white', edgecolor='black')
    plt.subplots_adjust(top=0.85, bottom=0.2)
    # Adjust layout to avoid clipping
    plt.tight_layout()

    return fig

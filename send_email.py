# Standard Library Imports
import logging
from datetime import datetime
import base64
import json
import io, os
import shutil
import pandas as pd

# External Libraries
import requests
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import ImageFont, ImageDraw, Image

# Azure Functions
import azure.functions as func

# Custom Modules (Assumed to be local)
from socialMedia import get_social_media_platform_data, create_social_media_platform_bar_chart
from summary import create_top_property_bar_chart, get_top_fixtures, create_top_fixtures_bar_chart, create_bar_chart, get_monthly_totals, create_monthly_totals_line_plot
from telegram import (get_telegram_platform_data, get_top_telegram_property, calculate_telegram_summary,
                      get_telegram_top_fixtures, create_telegram_top_fixtures_bar_chart,
                      telegram_domains_by_subscribers, create_treemap_chart_telegram, 
                      create_enhanced_matchday_line_plot, aggregate_matchday_data,
                      telegram_monthly_totals_line_plot, telegram_monthly_totals, 
                      top_fixtures_donut_chart, top_fixtures_graph_donut_chart, 
                      create_channel_type_pie_chart)



def sendEmail_function(combinedVar):
    
    try:
        # Load Fonts
        # font_path_large = "./Fonts/Supplemental/Arial.ttf"
        # font_path_medium = "./Fonts/Supplemental/Arial.ttf"
        font_path_large = "Fonts/Supplemental/Arial.ttf"
        font_path_medium = "Fonts/Supplemental/Arial.ttf"

        font_large = ImageFont.truetype(font_path_large, 70)
        font_medium = ImageFont.truetype(font_path_medium, 40)
        font_small = ImageFont.truetype(font_path_medium, 30)
    except OSError:
        print("Arial font not found. Using default font.")
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Ensure the pdf_output directory exists
    pdf_output_dir = "./pdf_output"
    os.makedirs(pdf_output_dir, exist_ok=True)

    # Delete all files in the pdf_output directory before creating new ones
    for filename in os.listdir(pdf_output_dir):
        file_path = os.path.join(pdf_output_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)  # Remove the file
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove directory and its contents
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Define the PDF output file path with the current date and time
    pdf_file_path = os.path.join(pdf_output_dir, f"Antipiracy_latest_report_on_{current_time}.pdf")
    print(pdf_file_path)

    
    with PdfPages(pdf_file_path) as pdf:
        # Create First Page
        first_page = create_attractive_page(
            title_text="Welcome to the Dazn Anti-Piracy Team dashboard",
            font_large=font_large,
            font_medium=font_medium,
            font_small=font_small,
            logo_path="static/Dazn-logo.png",
            background_color="#52387E",
        )
        pdf.savefig(ImageToPDF(first_page))  # Save to PDF

        figure_functions = [
            lambda: create_bar_chart(combinedVar),
            lambda: create_top_fixtures_bar_chart(get_top_fixtures(combinedVar)),
            lambda: create_monthly_totals_line_plot(get_monthly_totals(combinedVar)),
            lambda: create_social_media_platform_bar_chart(get_social_media_platform_data(combinedVar)),
            lambda: create_enhanced_matchday_line_plot(aggregate_matchday_data(combinedVar)),
            lambda: create_telegram_top_fixtures_bar_chart(get_telegram_top_fixtures(combinedVar)),
            lambda: create_top_property_bar_chart(get_top_telegram_property(combinedVar)),
            lambda: create_treemap_chart_telegram(telegram_domains_by_subscribers(combinedVar)),
            lambda: telegram_monthly_totals_line_plot(telegram_monthly_totals(combinedVar)),
            lambda: top_fixtures_graph_donut_chart(top_fixtures_donut_chart(combinedVar)),
            lambda: create_channel_type_pie_chart(combinedVar)

        ]

        # Dashboard
        

        for create_figure in figure_functions:         
            fig = create_figure()  # Generate chart
            #plt.figtext(0.5, 0.01, f"Chart {idx + 1} - Description goes here.", ha="center", fontsize=12, color="gray")
            try:
                pdf.savefig(fig, bbox_inches='tight')  # Save directly to the PDF
            except:
                isinstance(fig, go.Figure)
                img_bytes = fig.to_image(format="png", engine="kaleido", scale=5)
                image = Image.open(io.BytesIO(img_bytes))
                plt_fig, ax = plt.subplots(figsize=(12, 6))
                ax.axis('off')  # Hide axes for Plotly figures
                ax.imshow(image)  # Display the figure
                pdf.savefig(plt_fig)  # Save Plotly image as PDF page
                plt.close(plt_fig)

        # Create Last Page
        last_page = create_attractive_page(
            title_text="Thank You for Using the Dashboard",
            font_large=font_large,
            font_medium=font_medium,
            font_small=font_small,
            logo_path="static/Dazn-logo.png",
            background_color="#52387E",
        )

        pdf.savefig(ImageToPDF(last_page))  # Save to PDF

        # After PDF is created successfully, trigger email sending function
        send_exposure_report()


def create_attractive_page(
    title_text, font_large, font_medium, font_small, logo_path, background_color
):
    """Create a visually appealing page with a title, subtitle, and footer."""
    # Create a blank image
    page_width, page_height = 1600, 1200
    page = Image.new("RGB", (page_width, page_height), background_color)
    draw = ImageDraw.Draw(page)

    title_main = title_text.split("\n")  # Split the title into multiple lines
    # Draw each line separately with increasing Y positions
    y_position = 200  # Initial Y position
    for line in title_main:
        draw.text((100, y_position), line, fill="white", font=font_large)
        y_position += 100  # Increase Y position for the next line

    # Add Logo
    try:
        logo = Image.open(logo_path).resize((150, 150))
        page.paste(logo, (page_width - 200, 50))  # Position the logo
    except Exception as e:
        print(f"Logo could not be loaded: {e}")

    return page


# Helper Function to Convert PIL Image to Matplotlib Figure
def ImageToPDF(img):
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.axis("off")
    ax.imshow(img)
    return fig


# Define the function to get recipients and CC addresses
def get_credentials():
    # Load the Excel configuration file
    df = pd.read_excel(r"config/configuration_file.xlsx", sheet_name='mailer')
    
    # Extract email addresses
    to_addresses = (
        str(df['ToAddress'][0]).split(",") if not pd.isna(df['ToAddress'][0]) else []
    )
    cc_addresses = (
        str(df['CC_Address'][0]).split(",") if not pd.isna(df['CC_Address'][0]) else []
    )
    
    # Return the lists
    return to_addresses, cc_addresses


# Get dynamic recipients and CC recipients
to_addresses, cc_addresses = get_credentials()

to_addresses_str = ",".join(to_addresses) if to_addresses else None
cc_addresses_str = ",".join(cc_addresses) if cc_addresses else None

def send_exposure_report():
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Get current month in the format 'Month Year' (e.g., "October 2024")
    current_month = datetime.now().strftime("%B %Y")

    # Example of HTML email content with dynamic month insertion
    html_email = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h1 style="color: #0047ab;">Exposure Score Report - {current_month}</h1>
                <p>Hi Team,</p>
                <p>
                    Please find attached the detailed exposure score report for League 1 matches in the attached PDF.
                </p>
                <p>
                    Our team has diligently monitored various online platforms, including:
                    <ul>
                        <li>Pirate websites</li>
                        <li>Social media channels</li>
                        <li>User-generated content platforms</li>
                        <li>Telegram groups</li>
                        <li>App stores</li>
                    </ul>
                </p>
                <p>
                    We have identified and swiftly addressed any infringements to safeguard our content and ensure compliance with industry standards. 
                    Your feedback on these efforts is highly valued.
                </p>
                <p>
                    Should you have any questions or require further insights, please do not hesitate to reach out.
                </p>
                <p>
                    Best regards,<br>
                    <b>Manoj Kumar</b><br>
                    Anti-Piracy Team<br>
                </p>
            </body>
        </html>
        """

    # Define the path to the pdf_output folder
    pdf_output_dir = "./pdf_output"
    attachments = []

    # Gather all files in the pdf_output directory
    for filename in os.listdir(pdf_output_dir):
        file_path = os.path.join(pdf_output_dir, filename)
        if os.path.isfile(file_path):  # Only attach files, ignore directories
            try:
                # Read the file content
                with open(file_path, "rb") as f:
                    file_content = f.read()
                    # Base64 encode the file content
                    file_base64 = base64.b64encode(file_content).decode("utf-8")
                    attachments.append({
                        "attachment_content": file_base64,
                        "attachment_filename": filename  # Use the filename as is
                    })
            except Exception as e:
                logging.error(f"Error reading file {filename}: {e}")

    if not attachments:
        logging.error("No files found in the pdf_output directory.")
        return

    selected_attachment = attachments[0]


    # Construct the POST request data
    post_data = {
        "recipients": to_addresses_str,
        "cc": cc_addresses_str,
        "subject": f"Exposure Score Report - {current_month}",
        "message_content": html_email,
        "attachment_content": selected_attachment["attachment_content"],
        "attachment_filename": selected_attachment["attachment_filename"],  # Use filename directly
        "function_name": "la-security-secops-email-endpoint-prod-northeurope",
        "verify_string": "2de87331-4c38-4c$$0-bbc2-d1b6dfb63d3b-#skbdhbf"
    }

    # Azure Logic App endpoint URL
    post_url = "https://prod-43.northeurope.logic.azure.com:443/workflows/b9ccb16083f04f6bb07a9679303a7ffd/triggers/HTTPReceived/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FHTTPReceived%2Frun&sv=1.0&sig=VVYJDahy4jEeF4NpFqBuZgTHh1cFZ5L0lAcBIv6MuWY"

    # Send HTTP POST request
    try:
        response = requests.post(post_url, json=post_data)
        response.raise_for_status()  # Raises an HTTPError if the response code is 4xx/5xx
        logging.info(f"HTTP POST request sent successfully. Status code: {response.status_code}")
        print("Email sent successfully 200")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending HTTP POST request: {str(e)}")


def send_exceldata_report():
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Get current month in the format 'Month Year' (e.g., "October 2024")
    current_month = datetime.now().strftime("%B %Y")

    # Example of HTML email content with dynamic month insertion
    html_email = fhtml_email = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>Hi Team,</p>
                <p>
                    Please find attached the detailed exposure score report for League 1 matches in the attached excel for your data.
                </p>
                <p>
                    We have identified and swiftly addressed any infringements to safeguard our content and ensure compliance with industry standards. 
                    Your feedback on these efforts is highly valued.
                </p>
                <p>
                    Should you have any questions or require further insights, please do not hesitate to reach out.
                </p>
                <p>
                    Best regards,<br>
                    <b>Manoj Kumar</b><br>
                    Anti-Piracy Team<br>
                </p>
            </body>
        </html>
        """


    # Example of base64-encoded Excel content (replace with actual base64 content of the file)
    # Define the path to the pdf_output folder
    pdf_output_dir = "./excel_output"
    attachments = []
    # Gather all files in the pdf_output directory
    for filename in os.listdir(pdf_output_dir):
        file_path = os.path.join(pdf_output_dir, filename)
        if os.path.isfile(file_path):  # Only attach files, ignore directories
            try:
                # Read the file content
                with open(file_path, "rb") as f:
                    file_content = f.read()
                    # Base64 encode the file content
                    file_base64 = base64.b64encode(file_content).decode("utf-8")
                    attachments.append({
                        "attachment_content": file_base64,
                        "attachment_filename": filename
                    })
                    # Append the file details to the attachments list
            except Exception as e:
                logging.error(f"Error reading file {filename}: {e}")

    if not attachments:
        logging.error("No Excel files found for attachment.")
    else:
        # Select the first attachment (or iterate over `attachments` for multiple attachments)
        selected_attachment = attachments[0]
        print(selected_attachment)



        # Construct the POST request data
        post_data = {
            "recipients": to_addresses_str, 
            'cc':cc_addresses_str,
            "subject": f"Exposure Score Report - {current_month}", 
            "message_content": html_email,
            "attachment_content": selected_attachment["attachment_content"],
            "attachment_filename": f"{selected_attachment["attachment_filename"]}",
            "function_name": "la-security-secops-email-endpoint-prod-northeurope",
            "verify_string": "2de87331-4c38-4c$$0-bbc2-d1b6dfb63d3b-#skbdhbf"
        }

        # Azure Logic App endpoint URL
        post_url = "https://prod-43.northeurope.logic.azure.com:443/workflows/b9ccb16083f04f6bb07a9679303a7ffd/triggers/HTTPReceived/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FHTTPReceived%2Frun&sv=1.0&sig=VVYJDahy4jEeF4NpFqBuZgTHh1cFZ5L0lAcBIv6MuWY"
        # Send HTTP POST request
        try:
            response = requests.post(post_url, json=post_data)
            response.raise_for_status()  # Raises an HTTPError if the response code is 4xx/5xx
            logging.info(f"HTTP POST request sent successfully. Status code: {response.status_code}")

            print("Email sent successfully 200")
            return func.HttpResponse("Email sent successfully.", status_code=200)  # Return success message and status code
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending HTTP POST request: {str(e)}")
            return func.HttpResponse(f"Error sending HTTP POST request: {str(e)}", status_code=500)  # Return error message and status code



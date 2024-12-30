import numpy as np
from werkzeug.utils import secure_filename
import logging
from tornado.ioloop import IOLoop
from flask import Flask, request, render_template, redirect, url_for
import os
import pandas as pd
import requests
import numpy as np
from werkzeug.utils import secure_filename
from threading import Thread
from datetime import datetime
from tornado.ioloop import IOLoop
from send_email import sendEmail_function
from bokeh.embed import server_document
from bokeh.server.server import Server
import panel as pn
from flask import Response
from send_email import send_exceldata_report
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for Matplotlib

# Custom modules
from socialMedia import get_social_media_platform_data, create_social_media_platform_bar_chart
from summary import (
    calculate_summary, create_top_property_bar_chart, get_top_fixtures, 
    create_top_fixtures_bar_chart, create_bar_chart, get_monthly_totals, 
    create_monthly_totals_line_plot
)
from telegram import (
    widgets, get_telegram_platform_data, get_top_telegram_property, calculate_telegram_summary, 
    get_telegram_top_fixtures, create_telegram_top_fixtures_bar_chart, 
    telegram_domains_by_subscribers, create_treemap_chart_telegram, 
    create_enhanced_matchday_line_plot, aggregate_matchday_data, 
    telegram_monthly_totals_line_plot, telegram_monthly_totals, 
    top_fixtures_donut_chart, top_fixtures_graph_donut_chart, 
    create_channel_type_pie_chart
)
from bokeh.embed import server_document

from flask_sockets import Sockets
import websocket

from bokeh.embed import server_document
from bokeh.server.server import Server
from flask import send_from_directory


# Function to run Panel server
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, static_folder=".venv/lib/python3.12/site-packages/panel/dist")

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] =UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'xlsx'}

# Initialize Panel
pn.extension(sizing_mode="stretch_width")

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/static/<path:filename>')
def serve_static(filename):
    static_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '.venv/lib/python3.12/site-packages/bokeh/server/static'
    )
    return send_from_directory(static_dir, filename)


sockets = Sockets(app)

@sockets.route('/dashboard/ws')
def bokeh_websocket(ws):
    bokeh_ws = websocket.create_connection('ws://127.0.0.1:5002/bokeh_app/ws')
    try:
        while not ws.closed:
            ws_message = ws.receive()
            bokeh_ws.send(ws_message)
            bokeh_message = bokeh_ws.recv()
            ws.send(bokeh_message)
    finally:
        bokeh_ws.close()


@app.route('/dashboard')
def dashboard():
    panel_script = server_document("http://127.0.0.1:5002/bokeh_app")
    return render_template("dashboard.html", script=panel_script)


# Route for file upload
@app.route('/')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    files = request.files.getlist('file')
    dataframes = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Load each sheet from the uploaded file
            sheets = [pd.read_excel(file_path, sheet_name=i).reset_index(drop=True) for i in range(5)]
            sheets = [df.loc[:, ~df.columns.duplicated()] for df in sheets]
            
            # Add sheet names to each sheet's data
            sheet_names = ['Infringing_urls', 'Source_urls', 'Telegram', 'SocialMediaPlatforms', 'MobileApplications']
            for i, name in enumerate(sheet_names):
                sheets[i]['SheetName'] = name
            dataframes.extend(sheets)
    
    combined_data = pd.concat(dataframes, ignore_index=True)
    
    # Clean and process the data
    combined_data['propertyname'] = combined_data['propertyname'].fillna('Unknown')
    combined_data['fixtures'] = combined_data['fixtures'].fillna('Unknown')
    combined_data['DomainName'] = combined_data['DomainName'].fillna('Unknown')
    combined_data['URL'] = combined_data['URL'].fillna('Unknown')
    combined_data['Status'] = combined_data['Status'].fillna('Pending')
    combined_data['Identification Timestamp'] = pd.to_datetime(combined_data['Identification Timestamp'], errors='coerce')
    combined_data = combined_data.dropna(subset=['Identification Timestamp'])

    # Start the Panel server with the processed data
    thread = Thread(target=run_panel_server, args=(combined_data,))
    thread.daemon = True
    thread.start()

    # Redirect to the dashboard
    return redirect(url_for('dashboard'))



# Function to create the Panel dashboard
def create_dashboard(combined_data):

    dashboard_css = """
    body {
        background: linear-gradient(135deg, #eef2f3, #cfd9df);
        color: #333333;
        font-family: 'Arial', sans-serif;
    }
    .pn-widget-box, .pn-widget-select, .pn-widget-multichoice {
        background-color: #ffffff !important;
        border-radius: 8px;
        box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
        padding: 10px;
    }
    .pn-widget-button {
        background-color: #007bff !important;
        color: white !important;
        border-radius: 6px;
        font-weight: bold;
        padding: 8px 16px;
    }
    .pn-widget-button:hover {
        background-color: #0056b3 !important;
    }
    .pn-card {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.1);
        padding: 10px;
    }
    .header-text {
        color: #0056b3;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        padding: 10px;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 8px;
    }
    """

    loading_css = """
    .loading-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .spinner {
        display: flex;
        flex-direction: column;
        align-items: center;
        color: white;
        font-size: 1.5em;
    }

    .circular {
        animation: rotate 2s linear infinite;
    }

    .path {
        stroke: #ffffff;
        stroke-linecap: round;
        animation: dash 1.5s ease-in-out infinite;
    }

    @keyframes rotate {
        100% {
            transform: rotate(360deg);
        }
    }

    @keyframes dash {
        0% {
            stroke-dasharray: 1, 200;
            stroke-dashoffset: 0;
        }
        50% {
            stroke-dasharray: 89, 200;
            stroke-dashoffset: -35px;
        }
        100% {
            stroke-dasharray: 89, 200;
            stroke-dashoffset: -124px;
        }
    }
    """
    pn.config.raw_css.append(dashboard_css)
    pn.config.raw_css.append(loading_css)

    pn.extension(sizing_mode="stretch_width")

    # Define a loading spinner
    loading_spinner = pn.indicators.LoadingSpinner(width=50, height=50, align="center")



    loading_overlay = pn.pane.HTML("""
            <div class="loading-overlay">
                <div>
                    <div class="spinner"></div>
                    <p>Loading, please wait...</p>
                </div>
            </div>
            <style>
                .loading-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                }

                .spinner {
                    border: 8px solid rgba(255, 255, 255, 0.3);
                    border-top: 8px solid #ffffff;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                .loading-overlay p {
                    color: white;
                    font-size: 18px;
                    margin-top: 20px;
                    font-weight: bold;
                    text-align: center;
                }
            </style>
        """, visible=False, sizing_mode="stretch_both")


    css = """
    body {
        background: linear-gradient(135deg, #e8f1f2, #d9dce4, #b7c2d2);
        background-attachment: fixed;
        color: #333333;
    }
    .pn-widget-box, .pn-widget-select, .pn-widget-multichoice {
        background-color: #ffffff !important;
        border-radius: 10px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        color: #333333 !important;
        font-size: 14pt !important;
        padding: 8px !important;
    }
    .pn-widget-button {
        background-color: #0078a8 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
        font-weight: bold;
        padding: 8px 16px;
        transition: background-color 0.3s ease;
    }
    .pn-widget-button:hover {
        background-color: #005f73 !important;
    }
    /* Header text style for visibility */
    .header-text {
        color: #005f73 !important;
        font-size: 28px;
        font-weight: bold;
        padding: 10px;
        text-align: center;
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 8px;
        margin-bottom: 15px;
    }
    /* Label style for filters */
    .filter-label {
        color: #ffffff !important;
        font-weight: bold;
        background-color: #0078a8;
        padding: 8px;
        border-radius: 8px;
        text-align: center;
    }
    """

    pn.config.raw_css.append(css)


    # Filter Widgets
    propertyname_filter = pn.widgets.Select(name='Property Name', options=['All'] + list(combined_data['propertyname'].unique()))
    fixtures_filter = pn.widgets.MultiChoice(name='Select Fixtures', options=list(combined_data['fixtures'].unique()), height=100)
    start_date_filter = pn.widgets.DatetimePicker(name='Start Date', value=combined_data['Identification Timestamp'].min())
    end_date_filter = pn.widgets.DatetimePicker(name='End Date', value=combined_data['Identification Timestamp'].max())
    # Define two separate buttons for each section
    apply_summary_button = pn.widgets.Button(name="Apply Summary Filters", button_type="primary", width=150)
    apply_telegram_button = pn.widgets.Button(name="Apply Telegram Filters", button_type="primary", width=150)
    sent_email = pn.widgets.Button(name="Send Mail", button_type="primary", width=150)

    # Create the Social Media Platforms grouped bar chart pane

    # Summary display widgets styled as cards

    total_properties_card = pn.Card(
        pn.indicators.Number(value=0, format="{value}", font_size="20pt"),
        title="Total Properties", width=150, margin=(5, 5)
    )

    total_fixture_card = pn.Card(
        pn.indicators.Number( value=0, format="{value}", font_size="20pt"),
        title="Total Fixtures", width=150, margin=(5, 5)
    )

    total_infringements_card = pn.Card(
        pn.indicators.Number(value=0, format="{value}", font_size="20pt"),
        title="Total Infringements", width=150, margin=(5, 5)
    )

    number_of_websites_card = pn.Card(
        pn.indicators.Number( value=0, format="{value}", font_size="20pt"),
        title="Total Websites", width=150, margin=(5, 5)
    )

    removal_percentage_card = pn.Card(
        pn.indicators.Number( value=0, format="{value:.2f}%", font_size="20pt"),
        title="% Removal", width=150, margin=(5, 5)
    )


    # Summary Section with centered layout
    summary_section = pn.Row(
        total_properties_card,
        total_fixture_card,
        total_infringements_card,
        number_of_websites_card,
        removal_percentage_card,
        align="center",
        sizing_mode="stretch_width",
        margin=(10, 0, 20, 0)
    )

    # telegram section with cnetred layout 
    total_properties_telegram_card, total_fixture_telegram_card,total_infringements_telegram_card,number_of_websites_telegram_card,removal_percentage_telegram_card,views_incurred_card,no_of_channels_suspended_card,total_subscribers_card,impacted_subscribers_card, dashboard= widgets()

    telegram_section = pn.Row(
        total_properties_telegram_card,
        total_fixture_telegram_card,
        total_infringements_telegram_card,
        number_of_websites_telegram_card,
        removal_percentage_telegram_card,
        views_incurred_card,
        no_of_channels_suspended_card,
        total_subscribers_card,
        impacted_subscribers_card,
        align="center",
        sizing_mode="stretch_width",
        margin=(10, 0, 20, 0)
    )        


    # Create the Export to Excel button
    export_button = pn.widgets.Button(name="Export to Excel", button_type="primary", width=150)

    # Define the export function
    def export_to_excel(event):
        excel_output_dir = "./excel_output"
        try:
            files_deleted = False  # Flag to check if any files were deleted
            for filename in os.listdir(excel_output_dir):
                file_path = os.path.join(excel_output_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logging.info(f"Deleted old file: {filename}")
                    files_deleted = True
            if not files_deleted:
                logging.info("No old files found. Proceeding with creating a new file.")
        except Exception as e:
            logging.error(f"Error deleting old files: {e}")
        # Use the current value of `data_table` to get the filtered data
        filtered_data = data_table.value
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"excel_output/filtered_data_{timestamp}.xlsx"
        filtered_data.to_excel(file_path, index=False)
        send_exceldata_report()
        
        print("Data exported to Excel:", file_path)

    # Link the export function to the button click event
    export_button.on_click(export_to_excel)

    # Update summary and chart display function
    def update_summary(event=None):

     
        loading_overlay.visible = True
        pn.io.push_notebook()  # Ensure UI updates immediately

        filtered_data = combined_data
        selected_property = propertyname_filter.value
        selected_fixtures = fixtures_filter.value
        start_date = start_date_filter.value
        end_date = end_date_filter.value

        if selected_property != 'All':
            filtered_data = filtered_data[filtered_data['propertyname'] == selected_property]
        if selected_fixtures:
            filtered_data = filtered_data[filtered_data['fixtures'].isin(selected_fixtures)]
        if start_date and end_date:
            filtered_data = filtered_data[(filtered_data['Identification Timestamp'] >= start_date) &
                                        (filtered_data['Identification Timestamp'] <= end_date)]
        
        total_properties, total_fixture, total_infringements, number_of_websites, removal_percentage = calculate_summary(filtered_data)
        total_properties_card[0].value = total_properties
        total_fixture_card[0].value = total_fixture
        total_infringements_card[0].value = total_infringements
        number_of_websites_card[0].value = number_of_websites
        removal_percentage_card[0].value = removal_percentage


        # Update the charts only when the "Apply" button is clicked
        bar_chart.object = create_bar_chart(filtered_data, selected_property, ", ".join(selected_fixtures) if selected_fixtures else "All Fixtures")
        bar_chart_top_fixtures.object = create_top_fixtures_bar_chart(get_top_fixtures(filtered_data))
        line_chart_monthly.object = create_monthly_totals_line_plot(get_monthly_totals(filtered_data))
        # Generate social media platform chart after applying filters
        social_media_platform_chart.object = create_social_media_platform_bar_chart(get_social_media_platform_data(filtered_data))
        
        matchday_wisereport.object = create_enhanced_matchday_line_plot(aggregate_matchday_data(filtered_data))
        
        # Update the data table with filtered data
        data_table.value = filtered_data 

        loading_overlay.visible = False
        pn.io.push_notebook()


    apply_summary_button.on_click(update_summary)


    # Update summary and chart display function
    def telegramUpdate_summary(event=None):

        loading_overlay.visible = True
        pn.io.push_notebook()

        # Apply filters to the data
        filtered_data = combined_data[combined_data['SheetName'] == 'Telegram']
        selected_property = propertyname_filter.value
        selected_fixtures = fixtures_filter.value
        start_date = start_date_filter.value
        end_date = end_date_filter.value


        if selected_property != 'All':
            filtered_data = filtered_data[filtered_data['propertyname'] == selected_property]
        if selected_fixtures:
            filtered_data = filtered_data[filtered_data['fixtures'].isin(selected_fixtures)]
        if start_date and end_date:
            filtered_data = filtered_data[(filtered_data['Identification Timestamp'] >= start_date) &
                                        (filtered_data['Identification Timestamp'] <= end_date)]
        
        # Update Telegram-specific summary using provided variables
        impacted_subscribers, total_subscribers, no_of_channels_suspended, total_fixture_telegram, \
        total_infringements_telegram, total_properties_telegram, total_telegram_channel_names, \
        removal_percentage_telegram, views_incurred = calculate_telegram_summary(filtered_data)


        # Assign the returned values to the Telegram-specific summary cards
        impacted_subscribers_card[0].value = impacted_subscribers
        print(impacted_subscribers_card[0].value)
        total_subscribers_card[0].value = total_subscribers
        no_of_channels_suspended_card[0].value = no_of_channels_suspended
        total_fixture_telegram_card[0].value = total_fixture_telegram
        total_infringements_telegram_card[0].value = total_infringements_telegram
        total_properties_telegram_card[0].value = total_properties_telegram
        number_of_websites_telegram_card[0].value = total_telegram_channel_names
        removal_percentage_telegram_card[0].value = removal_percentage_telegram
        views_incurred_card[0].value = views_incurred

        unique_fixtures_telegram = filtered_data['fixtures'].unique().tolist()
        fixtures_filter.options = unique_fixtures_telegram 

        # Update the charts only when the "Apply" button is clicked
        topfixtures_telegram_barchart.object = create_telegram_top_fixtures_bar_chart(get_telegram_top_fixtures(filtered_data))
        telegram_chart_top_properties.object = create_top_property_bar_chart(get_top_telegram_property(filtered_data))
        topDomains_telegram_bySubscribers.object = create_treemap_chart_telegram(telegram_domains_by_subscribers(filtered_data))
        telegram_line_graph_plot.object = telegram_monthly_totals_line_plot(telegram_monthly_totals(filtered_data))
        top_fixture_donut_plot.object = top_fixtures_graph_donut_chart(top_fixtures_donut_chart(filtered_data))
        telegram_channeltype_chart.object = create_channel_type_pie_chart(filtered_data)
        # Update the data table with filtered data
        data_table.value = filtered_data

        loading_overlay.visible = False
        pn.io.push_notebook()

    def refresh_tab(event):
        try:
            if event.new == 0:  # "Summary" tab index
                if not bar_chart.object:
                    update_summary()
            elif event.new == 2:  # "Telegram" tab index
                if not telegram_chart_top_properties.object:
                    telegramUpdate_summary()
            else:
                print(f"Switched to tab {event.new}.")
        except Exception as e:
            print(f"Error switching tabs: {e}")


    # Link this function to the relevant button or event handler
    apply_telegram_button.on_click(telegramUpdate_summary)

    # Display initial DataFrame and empty charts
    data_table = pn.widgets.DataFrame(combined_data, min_width=500, min_height=500, sizing_mode="stretch_width")

    # Initialize Matplotlib chart panes as None, they will be updated after applying filters
    bar_chart = pn.pane.Matplotlib(None, sizing_mode="stretch_width")
    bar_chart_top_fixtures = pn.pane.Matplotlib(None, sizing_mode="stretch_width")
    line_chart_monthly = pn.pane.Matplotlib(None, sizing_mode="stretch_width")
    telegram_chart_top_properties = pn.pane.Matplotlib(None, sizing_mode="stretch_width")
    social_media_platform_chart = pn.pane.Matplotlib(None, sizing_mode="stretch_width")

    matchday_wisereport = pn.pane.Matplotlib(None, sizing_mode="stretch_width")

    # Initialize Plotly chart pane as None, it will be updated after applying filters
    topfixtures_telegram_barchart = pn.pane.Plotly(None, sizing_mode="stretch_width")
    top_fixture_donut_plot = pn.pane.Plotly(None, sizing_mode="stretch_width")
    telegram_channeltype_chart = pn.pane.Plotly(None, sizing_mode="stretch_width")
    # this is for top domains graph
    topDomains_telegram_bySubscribers = pn.pane.Plotly(None, sizing_mode="stretch_width")
    telegram_line_graph_plot = pn.pane.Matplotlib(None, sizing_mode="stretch_width")


    # Header Section with Title
    header = pn.Row(
        pn.pane.Markdown("<h2 class='header-text'>DAZN Interactive Dashboard</h2>"),
        #pn.pane.GIF("DAZN1.gif", width=100, height=100, margin=(0, 10, 0, 0)),
        align="center", sizing_mode="stretch_width", margin=(5, 5, 10, 5) 
    )

    # Filters Section with layout adjustments
    filters_section = pn.Row(
        pn.Column(pn.pane.Markdown("<div class='filter-label'>Start Date</div>"), start_date_filter, width=250, height=120, margin=(5, 10)),
        pn.Column(pn.pane.Markdown("<div class='filter-label'>End Date</div>"), end_date_filter, width=250, height=120, margin=(5, 10)),
        pn.Column(pn.pane.Markdown("<div class='filter-label'>Property Name</div>"), propertyname_filter, width=250, height=120, margin=(5, 10)),
        pn.Column(pn.pane.Markdown("<div class='filter-label'>Fixtures</div>"), fixtures_filter, width=250, height=120, margin=(5, 10)),
        pn.Column(apply_summary_button, width=150, height=80, align="center"),
        pn.Spacer(width=20),
        pn.Column(sent_email, width=150, height=80, align="center"),
        margin=(20, 0), align="center", sizing_mode="stretch_width"
    )

    telegram_filters_section = pn.Row(
        pn.Column(pn.pane.Markdown("<div class='filter-label'>Start Date</div>"), start_date_filter, width=250, height=120, margin=(5, 10)),
        pn.Column(pn.pane.Markdown("<div class='filter-label'>End Date</div>"), end_date_filter, width=250, height=120, margin=(5, 10)),
        pn.Column(pn.pane.Markdown("<div class='filter-label'>Property Name</div>"), propertyname_filter, width=250, height=120, margin=(5, 10)),
        pn.Column(pn.pane.Markdown("<div class='filter-label'>Fixtures</div>"), fixtures_filter, width=250, height=120, margin=(5, 10)),
        pn.Column(apply_telegram_button, width=150, height=80, align="center"),  # Telegram-specific Apply button
        pn.Spacer(width=20),
        pn.Column(sent_email, width=150, height=80, align="center"),
        margin=(20, 0), align="center", sizing_mode="stretch_width"
    )


    dashboard_tabs = pn.Tabs(
        ("Summary", pn.Column(
            header,
            filters_section,
            loading_overlay,
            summary_section,
            pn.Row(
                bar_chart,
                bar_chart_top_fixtures,
                sizing_mode="stretch_width",
                height=450,  # Set the same height for consistency
                margin=(5, 5)  # No margins
            ),
            pn.Row(
                line_chart_monthly,
                social_media_platform_chart,
                sizing_mode="stretch_width",
                height=450,  # Same height as the previous row
                margin=(5, 5)  # No margins
            ),
            pn.Row(
                matchday_wisereport,
                sizing_mode="stretch_width",
                height=450,  # Consistent height
                margin=(5, 5)  # No margins
            ),
            sizing_mode="stretch_width",
            margin=(5, 5)  # Minimal margin
        )),
        ("Data Table", pn.Column(
            data_table,
            pn.Column(export_button, align="end"),
            loading_overlay,
            sizing_mode="stretch_width",
            margin=(5, 5)  # Minimal margin
        )),
        ("Telegram", pn.Column(
            header,
            telegram_filters_section,
            loading_overlay,
            telegram_section,
            topfixtures_telegram_barchart,
            pn.Row(
                topDomains_telegram_bySubscribers,
                telegram_chart_top_properties,
                sizing_mode="stretch_width",
                height=450,  # Uniform height
                margin=(5, 5)  # No margins
            ),
            pn.Row(
                telegram_channeltype_chart,
                top_fixture_donut_plot,
                sizing_mode="stretch_width",
                height=450,  # Consistent height
                margin=(5, 5)  # No margins
            ),
            pn.Row(
                telegram_line_graph_plot,
                sizing_mode="stretch_width",
                height=450,  # Consistent height
                margin=(5, 5)  # No margins
            ),
            
            sizing_mode="stretch_width",
            margin=(5, 5)  # Minimal margin
        )),
    )

    sent_email.on_click(lambda event: sendEmail_function(combined_data))

    dashboard_tabs.param.watch(refresh_tab, 'active')
       
    return dashboard_tabs


# Function to run the Panel server
def run_panel_server(combined_data):
    def modify_doc(doc):
        dashboard = create_dashboard(combined_data)
        dashboard.server_doc(doc)

    try:
        server = Server(
            {'/bokeh_app': modify_doc},
            port=5002, 
            
            allow_websocket_origin=[
                "127.0.0.1:5000",
                "localhost:5000",
                "localhost:80",
                "127.0.0.1:80",
                "127.0.0.1:5002",
                "localhost:5002",
                "as-antipiracy-phase1-dev-eceje4dqddb7gbev.centralindia-01.azurewebsites.net",
                "as-antipiracy-phase1-dev-eceje4dqddb7gbev.centralindia-01.azurewebsites.net:80",
                "as-antipiracy-localtesting-dev-hvgdeqh4gceyedfh.centralindia-01.azurewebsites.net",
                "as-antipiracy-localtesting-dev-hvgdeqh4gceyedfh.centralindia-01.azurewebsites.net:80",
                "as-antipiracy-localtesting-dev-hvgdeqh4gceyedfh.centralindia-01.azurewebsites.net:443",
                "as-antipiracy-phase1-dev-eceje4dqddb7gbev.centralindia-01.azurewebsites.net:443"           
            ],
            address="0.0.0.0"
        )
        server.start()
        server.io_loop.start()
    except Exception as e:
        print(f"Error starting Panel server: {e}")



if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host="0.0.0.0", debug=True, port=5000, threaded=True)

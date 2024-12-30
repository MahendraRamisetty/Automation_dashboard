
import pandas as pd

# Updated `logic_func` implementation to capture unique property names and fixtures, and filter based on normalized values.
def logic_func(inputexcel_df):
    try:
        # Reading all sheets into a dictionary of DataFrames
        all_sheets = pd.read_excel(inputexcel_df, sheet_name=None)
    except Exception as ex:
        print(f"Error reading Excel file: {ex}")
        return [], {}

    unique_propertynames = set()  # Use a set to ensure unique values
    unique_fixtures = set()  # Use a set for unique fixtures across sheets
    processed_data = {}

    # Define normalized names for each sheet
    normalized_sheet_names = {
        "enforcement_sheet_infringing": "enforcement_sheet_infringing",
        "enforcement_sheet_source": "enforcement_sheet_source",
        "telegram": "telegram",
        "socialmediaplatforms": "socialmediaplatforms",
        "mobileapplications": "mobileapplications"
    }

    for sheet_name, normalized_name in normalized_sheet_names.items():
        # Check if sheet exists (case insensitive)
        matching_sheet_name = next((name for name in all_sheets.keys() if name.lower() == sheet_name), None)
        if matching_sheet_name:
            df = all_sheets[matching_sheet_name]
            print(f"\nProcessing sheet: {sheet_name}")

            # Normalize column names
            df.columns = df.columns.str.lower().str.strip()

            # Standardize 'propertyname' and 'fixtures' values (convert to lowercase and strip spaces)
            if 'propertyname' in df.columns:
                df['propertyname'] = df['propertyname'].str.lower().str.strip()
                unique_propertynames.update(df['propertyname'].unique().tolist())

            if 'fixtures' in df.columns:
                df['fixtures'] = df['fixtures'].str.lower().str.strip()
                unique_fixtures.update(df['fixtures'].unique().tolist())

            # Store each processed DataFrame by normalized sheet name
            processed_data[normalized_name] = df
            print(f"Sheet '{normalized_name}' added to processed_data.")
        else:
            print(f"Warning: Sheet '{sheet_name}' not found in the uploaded file.")

    # Convert sets to lists for easier manipulation later
    unique_propertynames = list(unique_propertynames)
    unique_fixtures = list(unique_fixtures)

    print("\nUnique property names:", unique_propertynames)
    print("Unique fixtures:", unique_fixtures)

    
    # Print both keys and the full content of each DataFrame in processed_data
    print("\nFinal processed data (keys and values):")
    for sheet_name, df in processed_data.items():
        print(f"\nSheet: {sheet_name}")
        print(df)  # This will print the entire DataFrame contents for each sheet

    return unique_propertynames, unique_fixtures, processed_data



def process_telegram_data(df, property_name=None, fixture=None, start_timestamp=None, end_timestamp=None):
    if df is None:
        print("Error: DataFrame for 'Telegram' sheet is None.")
        return {}
     # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    # Filter by property name if specified and 'propertyname' exists in columns
    
    # Normalize the values in the 'propertyname' column and the filter value
    if property_name:
        df = df[df['propertyname'].str.lower().str.strip() == property_name.lower().strip()]

    # Filter by fixture if specified
    if fixture and "fixtures" in df.columns:
        df["fixtures"] = df["fixtures"].str.lower().str.strip()
        df = df[df["fixtures"] == fixture.lower().strip()]

    # Filter by timestamp if specified
    if start_timestamp and end_timestamp and "identification timestamp" in df.columns:
        df["identification timestamp"] = pd.to_datetime(df["identification timestamp"], errors="coerce")
        df = df[(df["identification timestamp"] >= start_timestamp) & (df["identification timestamp"] <= end_timestamp)]

    
    # Perform calculations
    total_properties_count = df['propertyname'].nunique() if 'propertyname' in df.columns else 0
    unique_fixtures_count = df["fixtures"].str.lower().str.strip().nunique() if "fixtures" in df.columns else 0
    unique_url_count = df['url'].nunique() if 'url' in df.columns else 0

    df['status'] = df['status'].str.lower().str.strip()
    status_counts = df['status'].value_counts()
    total_approved_removed = status_counts.get('approved', 0) + status_counts.get('removed', 0)
    # Calculate removal percentage
    removal_percentage = (total_approved_removed / unique_url_count * 100) if unique_url_count > 0 else 0
    unique_channels = df['channelname'].unique().tolist() if 'channelname' in df.columns else []
    channel_count = len(unique_channels)
    total_views = df['views'].sum() if 'views' in df.columns else 0
    total_subscribers = df['channelsubscribers'].sum() if 'views' in df.columns else 0
    impacted_subscribers = df[df['status'].isin(['approved', 'removed'])]['channelsubscribers'].sum()


    result = {
        'total_properties_count': total_properties_count,
        'unique_url_count': unique_url_count,
        'total_approved_removed':total_approved_removed,
        'unique_fixtures_count':unique_fixtures_count,
        '% Removal': removal_percentage ,
        'channel_count': channel_count,
        'unique_channels': unique_channels,
        'total_views': total_views,
        'total_subscribers': total_subscribers,
        'impacted_subscribers': impacted_subscribers
    }

    return result


# Additional function for processing the Telegram sheet with property name and fixture filters
def process_telegram_data(df, property_name=None, fixture=None, start_timestamp=None, end_timestamp=None):
    if df is None:
        print("Error: DataFrame for 'Telegram' sheet is None.")
        return {}

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    # Filter by property name if specified
    if property_name:
        df = df[df['propertyname'].str.lower().str.strip() == property_name.lower().strip()]

    # Filter by fixture if specified
    if fixture:
        df = df[df['fixtures'].str.lower().str.strip() == fixture.lower().strip()]

    # Filter by timestamp if specified and 'identification timestamp' exists
    if start_timestamp and end_timestamp and 'identification timestamp' in df.columns:
        df['identification timestamp'] = pd.to_datetime(df['identification timestamp'], errors='coerce')
        df = df[(df['identification timestamp'] >= start_timestamp) & (df['identification timestamp'] <= end_timestamp)]

# Calculate unique property count by standardizing 'propertyname'
    total_properties_count = df["propertyname"].str.lower().str.strip().nunique() if "propertyname" in df.columns else 0
    unique_fixtures_count = df["fixtures"].str.lower().str.strip().nunique() if "fixtures" in df.columns else 0
    unique_url_count = df["url"].nunique() if "url" in df.columns else 0

    status_counts = df['status'].str.lower().str.strip().value_counts() if 'status' in df.columns else pd.Series()
    total_approved_removed = status_counts.get('approved', 0) + status_counts.get('removed', 0)

    # Calculate removal percentage
    removal_percentage = (total_approved_removed / unique_url_count * 100) if unique_url_count > 0 else 0
    unique_channels = df['channelname'].unique().tolist() if 'channelname' in df.columns else []
    channel_count = len(unique_channels)
    # Convert 'views' to numeric, coercing any non-numeric values to NaN, and then sum only valid integers
    total_views = pd.to_numeric(df['views'], errors='coerce').dropna().astype(int).sum() if 'views' in df.columns else 0

    total_subscribers = pd.to_numeric(df['channelsubscribers'], errors='coerce').dropna().astype(int).sum() if 'channelsubscribers' in df.columns else 0
    
    # Convert 'channelsubscribers' to numeric, coercing errors to NaN, and then sum
    impacted_subscribers = pd.to_numeric(df[df['status'].str.lower().isin(['approved', 'removed'])]['channelsubscribers'],errors='coerce').sum() if 'status' in df.columns and 'channelsubscribers' in df.columns else 0

    print(impacted_subscribers)


    result = {
        'total_properties_count': total_properties_count,
        'unique_fixtures_count': unique_fixtures_count,
        'unique_url_count': unique_url_count,
        'total_approved_removed':total_approved_removed,
        '% Removal': removal_percentage ,
        'channel_count': channel_count,
        'unique_channels': unique_channels,
        'total_views': total_views,
        'total_subscribers': total_subscribers,
        'impacted_subscribers': impacted_subscribers
    }

    return result
    

# Processing function for the SocialMediaPlatforms sheet
def process_socialmedia_data(df, property_name=None):
    if df is None:
        print("Error: DataFrame for 'SocialMediaPlatforms' sheet is None.")
        return {}

    if property_name and 'propertyname' in df.columns:
        df = df[df['propertyname'] == property_name]
    
    total_posts = df['posts'].sum() if 'posts' in df.columns else 0
    engagement_rate = df['engagement_rate'].mean() if 'engagement_rate' in df.columns else 0
    unique_accounts = df['accountname'].nunique() if 'accountname' in df.columns else 0
    
    result = {
        'total_posts': total_posts,
        'engagement_rate': engagement_rate,
        'unique_accounts': unique_accounts
    }
    return result

# Processing function for the MobileApplications sheet
def process_mobileapp_data(df, property_name=None):
    if df is None:
        print("Error: DataFrame for 'MobileApplications' sheet is None.")
        return {}

    if property_name and 'propertyname' in df.columns:
        df = df[df['propertyname'] == property_name]
    
    unique_apps = df['appname'].nunique() if 'appname' in df.columns else 0
    total_downloads = df['downloads'].sum() if 'downloads' in df.columns else 0
    
    result = {
        'unique_apps': unique_apps,
        'total_downloads': total_downloads
    }
    return result

# Core validation logic for HSN Agent

# import necessary libraries
import pandas as pd
import spacy
from collections import defaultdict

# Load the English NLP model for entity extraction (used in conversational input)
nlp = spacy.load("en_core_web_sm")

# Function to extract HSN code from free-form user text Used in the conversational /chat endpoint
def extract_hsn_from_text(text):
    text = text.strip()
    doc = nlp(text)
    codes = set()
    for token in doc:
        if token.like_num:
            value = token.text.strip()
            if value.isdigit() and len(value) in [2, 4, 6, 8]:
                codes.add(value)
    return list(codes)


# Global DataFrame to hold the Excel data
df = None

# Dictionary to track invalid HSNs and reasons
invalid_attempts = defaultdict(int)

# Function to load and clean Excel data, This can be reused to refresh the dataset dynamically (e.g., via an API endpoint)
def load_dataset():
    global df, invalid_attempts
    try:
        df = pd.read_excel('data/HSN_SAC.xlsx')
    except FileNotFoundError:
        raise FileNotFoundError("The Excel file 'HSN_SAC.xlsx' was not found.")
    except pd.errors.EmptyDataError:
        raise ValueError("The Excel file is empty or not formatted correctly.")
    except pd.errors.ParserError:
        raise ValueError("The Excel file is not formatted correctly or contains parsing errors.")
    except Exception as e:
        raise Exception(f"An error occurred while reading the Excel file: {e}")

    # Ensure the DataFrame is not empty
    if df.empty:
        raise ValueError("The Excel file is empty or not formatted correctly.")

    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    # Ensure the required columns exist
    if 'HSNCode' not in df.columns or 'Description' not in df.columns:
        raise ValueError("HSNCode and Description columns must be present in the Excel file.")

    # Ensure the HSNCode column is of string type for consistency
    df['HSNCode'] = df['HSNCode'].astype(str).str.strip()

    # Ensure the Description column is of string type for consistency
    df['Description'] = df['Description'].astype(str)

    # ✅ Clear old invalid attempts
    invalid_attempts.clear()

# Load the dataset once on startup
load_dataset()


def log_invalid_hsn(hsn_code, reason, tracker):
    key = f"{reason} | {hsn_code}"
    tracker[key] += 1

def get_invalid_hsn_summary(tracker):
    return sorted(tracker.items(), key=lambda x: x[1], reverse=True)

# Function to validate HSN hierarchy
# ADK Intent: ValidateHSNHierarchy
def validate_hierarchy(hsn_code):
    """
    Checks if parent HSN levels (2, 4, 6) exist for a given HSN code of length >= 2.
    Returns a dictionary of parent levels and their descriptions if found.
    """
    hsn_code = str(hsn_code).strip()
    length = len(hsn_code)

    # Only consider levels shorter than the given code (e.g., parents)
    levels = [l for l in [2, 4, 6] if l < length]
    
    hierarchy = {}
    for l in levels:
        prefix = hsn_code[:l]
        match = df[df['HSNCode'] == prefix]
        hierarchy[prefix] = match.iloc[0]['Description'] if not match.empty else "Not found"

    return hierarchy


# Function to validate a single HSN code
# ADK Intent: ValidateHSNCode
def validate_hsn(hsn_code):
    hsn_code = str(hsn_code).strip()

    # Format check
    if not hsn_code.isdigit() or len(hsn_code) not in [2, 4, 6, 8]:
        log_invalid_hsn(hsn_code, "Invalid format")
        return {"valid": False, "reason": "Invalid format"}

    # Existence check
    match = df[df['HSNCode'] == hsn_code]
    if not match.empty:
        description = match.iloc[0]['Description']
        result = {
            "valid": True,
            "description": description
        }

        # Optional: Add hierarchy if it's an 8- or 6-digit code
        if len(hsn_code) in [6, 8]:
            hierarchy = validate_hierarchy(hsn_code)
            result["hierarchy"] = {
                level: desc if desc else "Not found"
                for level, desc in hierarchy.items()
            }

        return result

    else:
        log_invalid_hsn(hsn_code, "HSN code not found", invalid_attempts)
        return {"valid": False, "reason": "HSN code not found"}


# Function to validate a list of HSN codes
# ADK Intent: ValidateHSNCodesList
def validate_hsn_list(hsn_list):
    return [{"hsn_code": hsn, "result": validate_hsn(hsn)} for hsn in hsn_list]

# Optional CLI test (can be used for manual testing)
if __name__ == "__main__":
    print(validate_hsn("1001"))
    print(validate_hsn_list(["0101", "789012", "345678"]))


import pandas as pd
import spacy
import os
import glob
import json
import re
import random  # For random name and phone numbers
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from reportlab.lib.units import inch

# Define the path to the "transcription" folder
transcription_folder_path = os.path.join(os.getcwd(), "transcriptions")

# Get a list of all text files in the "transcription" folder
text_files = glob.glob(os.path.join(transcription_folder_path, "*.txt"))
text_files = sorted(text_files)

#-------------------------#
# Load SpaCy model
nlp = spacy.load("de_core_news_sm")

# Define word numbers
word_numbers = ["ein", "eine", "einen", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn"]

# Preprocess texts
def preprocess(text):
    doc = nlp(text.lower())
    tokens = []
    for token in doc:
        if token.is_punct:  # Skip punctuation
            continue
        if token.is_digit or token.text in word_numbers:  # Preserve numbers and word numbers
            tokens.append(token.text)
        elif token.is_alpha and not token.is_stop:  # Lemmatize other alphabetic tokens
            tokens.append(token.lemma_)
    return " ".join(tokens)

# Define the file path
keywords_file_path = os.path.join(os.getcwd(), "keywords", "keywords_dict.json")

# Load the JSON file into keywords_dict
with open(keywords_file_path, "r", encoding="utf-8") as json_file:
    keywords_dict = json.load(json_file)
    
    
#-------------------------#
##RULE-BASED MODEL##

# Function to extract data with adjectives
def extract_details_german_with_adjectives(text):
    details = {
        "Project description": "",
        "Rooms": "",
        "Special features": "",
        "Design style": "",
        "Materials": "",
        "Budget": "",
        "Timeline": "",
    }
    
    # Parse the text
    details["Project description"] = text.split('\n')[0].strip()
    
    #----------------------#
    # Define the list of word-numbers
    word_numbers = ["ein", "eine", "einen", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn"]
    number_pattern = rf"(\b(?:\d+|{'|'.join(word_numbers)})\b)"  # Match numeric or word-numbers

    # Room keywords pattern
    room_keywords = "|".join(keywords_dict["ROOM_KEYWORDS"])

    # Regex to match rooms with number patterns and adjectives
    rooms_pattern = rf"{number_pattern}((?:\s+\b[\wäöüß]+\b)+)?\s+({room_keywords})"

    # Extract matches
    rooms_matches = re.findall(rooms_pattern, text, re.IGNORECASE)

    # Format the results
    details["Rooms"] = ", ".join([
        f"{num or ''} {adj.strip()} {room}".strip()
        for num, adj, room in rooms_matches
    ])
    #replace " und" with "," in the string
    details["Rooms"] = details["Rooms"].replace(" und", ",")        

    #-------------------------#
    
    # Special Features with adjectives
    features_keywords = "|".join(keywords_dict["SPECIAL_FEATURES_KEYWORDS"])  # Join keywords into a regex pattern
    features_pattern = rf"(\b[\wäöüß]+\b)?\s*({features_keywords})"  # Use rf-string for dynamic pattern creation
    features_matches = re.findall(features_pattern, text, re.IGNORECASE)

    # Format the matched features
    details["Special features"] = ", ".join([
        f"{adj or ''} {feature}".strip() for adj, feature in features_matches if feature
    ])
 
    #-------------------------# 
    # Design Style with adjectives
    style_keywords = "|".join(keywords_dict["DESIGN_STYLE_KEYWORDS"])  # Join keywords into a regex pattern
    style_pattern = rf"(\b[\wäöüß]+\b)?\s*({style_keywords})"  # Match an optional word (adjective) before the keyword
    style_matches = re.findall(style_pattern, text, re.IGNORECASE)

    # Format the matched design styles
    details["Design style"] = ", ".join([
        f"{adj or ''} {style}".strip() for adj, style in style_matches if style
    ])

    #-------------------------# 
    # Materials with adjectives
    material_keywords = "|".join(keywords_dict["MATERIALS_KEYWORDS"])  # Join keywords into a regex pattern
    material_pattern = rf"(\b[\wäöüß]+\b)?\s*({material_keywords})"  # Match an optional word (adjective) before the keyword
    material_matches = re.findall(material_pattern, text, re.IGNORECASE)

    # Format the matched materials
    details["Materials"] = ", ".join([
        f"{adj or ''} {material}".strip() for adj, material in material_matches if material
    ])
        
    #-------------------------#
    # Budget
    budget_pattern = r"([\d\s.,]+(?:€|Euro))"
    budget_match = re.search(budget_pattern, text, re.IGNORECASE)
    details["Budget"] = budget_match.group(0) if budget_match else ""
    
    #-------------------------#
    # Timeline
    timeline_pattern = r"(\d+ (?:Monat(?:en|e)?|Jahr(?:en|e)?|Woche(?:n)?))"
    timeline_match = re.search(timeline_pattern, text, re.IGNORECASE)
    details["Timeline"] = timeline_match.group(0) if timeline_match else ""
    
    # Define lists of articles and modal verbs
    articles = ["die", "das", "der", "ein", "eine", "einen", "einem", "einer", "den", "dem"]
    modal_verbs = ["sollte", "könnte", "wollte", "dürfte", "möchte", "müssen", "muss", "kann", "können", "sollen", "wollen", "dürfen"]

    # Compile regex patterns for articles and modal verbs
    articles_pattern = rf"\b(?:{'|'.join(articles)})\b"
    modal_verbs_pattern = rf"\b(?:{'|'.join(modal_verbs)})\b"

    # Remove articles and modal verbs
    def clean_text(text):
        text = re.sub(articles_pattern, "", text, flags=re.IGNORECASE)  # Remove articles
        text = re.sub(modal_verbs_pattern, "", text, flags=re.IGNORECASE)  # Remove modal verbs
        return re.sub(r"\s+", " ", text).strip()  # Normalize spaces

    # Apply cleanup to Design style
    details["Design style"] = clean_text(details["Design style"].replace(" und", ","))
    details["Materials"] = clean_text(details["Materials"].replace(" und", ","))

    return details

##-------##
# Random Data Generation
def generate_random_customer_name():
    first_names = ["Anna", "Max", "Laura", "Lukas", "Sophia", "Paul", "Mia", "Jonas", "Lea", "Felix"]
    last_names = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Hoffmann", "Schäfer"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_random_address():
    streets = ["Musterstraße", "Hauptstraße", "Gartenweg", "Bachstraße", "Schulweg", "Kirchplatz", "Am Dorf", "Lindenweg"]
    cities = ["Berlin", "Hamburg", "München", "Köln", "Frankfurt", "Stuttgart", "Düsseldorf", "Dortmund", "Essen", "Bremen"]
    return f"{random.choice(streets)} {random.randint(1, 200)}, {random.randint(10000, 99999)} {random.choice(cities)}"

def generate_random_phone():
    return f"+49-{random.randint(100, 999)}-{random.randint(1000, 9999)}-XXX"

def generate_random_client_name():
    return generate_random_customer_name()


# Random data
customer_name = generate_random_customer_name()
customer_address = generate_random_address()
customer_phone = generate_random_phone()
client_name = generate_random_client_name()

##--------##

## Extract data and generate csv and pdf-report
def generate_pdf_and_return_path(text, base_name):
    return os.path.relpath(pdf_file, os.getcwd())

for file in text_files:
    text = open(file, 'r', encoding='utf-8').read()
    report_dict = extract_details_german_with_adjectives(text)
    
    ## save CSV ##
    # Convert dictionary to DataFrame
    df = pd.DataFrame(list(report_dict.items()), columns=["Category", "Data"])
    # Save DataFrame to CSV
    output_csv_folder = os.path.join(os.getcwd(), "gen-csv-report")
    base_name = os.path.splitext(os.path.basename(file))[0]
    csv_file = os.path.join(output_csv_folder, f"{base_name}.csv")
    df.to_csv(csv_file, index=False, encoding="utf-8")
    
    ## Save PDF ##
    details = report_dict

    # Function to preprocess text for bullet points
    def preprocess_for_bullets(text):
        lines = [line.strip() for line in text.replace(",", "\n").split("\n")]
        return "\n".join([f"• {line[0].upper() + line[1:]}" for line in lines if line])

    # Preprocess table fields
    data = [
        ["Field", "Details"],
        ["Rooms", preprocess_for_bullets(details["Rooms"])],
        ["Special features", preprocess_for_bullets(details["Special features"])],
        ["Design style", preprocess_for_bullets(details["Design style"])],
        ["Materials", preprocess_for_bullets(details["Materials"])],
        ["Budget", details["Budget"]],
        ["Timeline", details["Timeline"]]
    ]

    output_pdf_folder = os.path.join(os.getcwd(), "static", "gen-pdf-report")
    base_name = os.path.splitext(os.path.basename(file))[0]
    pdf_file = os.path.join(output_pdf_folder, f"{base_name}.pdf")

    #return pdf path to main
    #generate_pdf_and_return_path(pdf_file, f"{base_name}.pdf")

    # Define PDF document with explicit margins
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, leftMargin=1*inch, rightMargin=1*inch, topMargin=1*inch, bottomMargin=1*inch)
    styles = getSampleStyleSheet()
    story = []

    # Calculate usable width
    usable_width = A4[0] - doc.leftMargin - doc.rightMargin

    # Logo Dimensions
    original_width = 1128
    original_height = 560
    desired_width = 200  # Set the desired width for the logo
    aspect_ratio = original_height / original_width  # Calculate aspect ratio
    calculated_height = desired_width * aspect_ratio  # Calculate height maintaining aspect ratio

    # Add Logo
    logo_path = "static/logo.png"  # Replace with your logo file
    logo = Image(logo_path, width=desired_width, height=calculated_height)
    story.append(logo)

    # Customer Details with Bullets
    story.append(Paragraph("<b>Customer Details:</b>", styles["Heading2"]))
    story.append(Paragraph(f"• Customer name: {customer_name}", styles["Normal"]))
    story.append(Paragraph(f"• Customer address: {customer_address}", styles["Normal"]))
    story.append(Paragraph(f"• Customer phone: {customer_phone}", styles["Normal"]))
    story.append(Spacer(1, 10))

    # Conversation Script
    story.append(Paragraph("<b>Conversation Script:</b>", styles["Heading2"]))
    story.append(Paragraph(details["Project description"], styles["Normal"]))
    story.append(Spacer(1, 10))

    # Report Summary
    story.append(Paragraph("<b>Report Summary:</b>", styles["Heading2"]))

    # Dynamically adjust table column widths based on content length
    col_widths = [0.2 * usable_width, 0.8 * usable_width]  # Adjust column widths (20% for 'Field', 80% for 'Details')
    
    # Add Table to the Story
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)
    story.append(Spacer(1, 10))

    # Client Name and Date-Time in Bottom-Left Corner
    current_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    story.append(Spacer(1, 50))  # Spacer to push the footer to the bottom
    footer_style = styles["Normal"]
    footer_style.alignment = 0  # Left align
    story.append(Paragraph(f"Client Name: {client_name}", footer_style))
    story.append(Paragraph(f"Date and Time: {current_datetime}", footer_style))

    # Build the PDF
    doc.build(story)

    # After successful processing, delete the transcription file
    try:
        os.remove(file)
        print(f"Deleted transcription file: {file}")
    except Exception as e:
        print(f"Error deleting file {file}: {e}")
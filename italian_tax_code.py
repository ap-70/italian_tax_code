from cat.mad_hatter.decorators import hook
from cat.experimental.form import form, CatForm
from pydantic import BaseModel, Field, field_validator

import datetime
import csv

csv_file = './cat/plugins/italian_tax_code/ComuniItalia.csv'
land_code = ""
birth_date = ""

# Function to extract consonants from a name or surname
def extract_consonants(s):
    return ''.join([char for char in s.upper() if char not in 'AEIOU'])

# Function to extract vowels from a name or surname
def extract_vowels(s):
    return ''.join([char for char in s.upper() if char in 'AEIOU'])

# Function to get the three characters for name or surname
def get_name_code(surname, is_name=False):
    consonants = extract_consonants(surname)
    vowels = extract_vowels(surname)

    if len(consonants) >= 3:
        if is_name:
            return consonants[0] + consonants[2] + consonants[3] if len(consonants) > 3 else consonants[:3]
        return consonants[:3]
    else:
        return (consonants + vowels)[:3].ljust(3, 'X')

# Function to get birth year code
def get_year_code(year):
    return str(year)[-2:]

# Function to get birth month code
def get_month_code(month):
    months = "ABCDEHLMPRST"
    return months[month - 1]

# Function to get birth day code, adjusted for gender
def get_day_code(day, gender):
    if gender.upper() == 'F':
        day += 40
    return str(day).zfill(2)

# Function to calculate the control character
def calculate_control_character(partial_code):
    # Character to value mapping for odd positions
    odd_values = {
        '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13, '6': 15, '7': 17, '8': 19, '9': 21,
        'A': 1, 'B': 0, 'C': 5, 'D': 7, 'E': 9, 'F': 13, 'G': 15, 'H': 17, 'I': 19, 'J': 21,
        'K': 2, 'L': 4, 'M': 18, 'N': 20, 'O': 11, 'P': 3, 'Q': 6, 'R': 8, 'S': 12, 'T': 14,
        'U': 16, 'V': 10, 'W': 22, 'X': 25, 'Y': 24, 'Z': 23
    }

    # Character to value mapping for even positions
    even_values = {
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9,
        'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19,
        'U': 20, 'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25
    }

    # Alphabet to get the control character
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Summing values based on position
    total_sum = 0
    for i, char in enumerate(partial_code):
        if (i + 1) % 2 == 0:
            total_sum += even_values[char]
        else:
            total_sum += odd_values[char]

    # Calculate control character
    control_index = total_sum % 26
    return alphabet[control_index]

# Function to calculate the fiscal code
def calculate_tax_id_code(name, surname, birth_date, gender, comune_code):
    # Extracting the date components
    birth_day = birth_date.day
    birth_month = birth_date.month
    birth_year = birth_date.year

    # Generate the fiscal code parts
    surname_code = get_name_code(surname)
    name_code = get_name_code(name, is_name=True)
    year_code = get_year_code(birth_year)
    month_code = get_month_code(birth_month)
    day_code = get_day_code(birth_day, gender)

    # Construct fiscal code(without the control character)
    partial_code = surname_code + name_code + year_code + month_code + day_code + comune_code

    # Calculate control character
    control_character = calculate_control_character(partial_code)

    # Return full fiscal code
    return partial_code + control_character

# Function to retrieve the cadastral code given the name of the municipality
def get_cadastral_code(comune_di_nascita, provincia):
    global land_code

    # Open CSV file
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
            
        # We cycle on the lines of the CSV
        for row in reader:
            # If the description of the municipality matches
            if row['SIGLA'].strip().lower() == provincia.strip().lower() and row['DESCRIZIONE COMUNE'].strip().lower() == comune_di_nascita.strip().lower():
                land_code = row['CODICE BELFIORE']
                return True
    land_code = ""
    # If we don't find the municipality
    return False

def validate_comune(comune_di_nascita):
    # Open CSV file
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
            
        # We cycle on the lines of the CSV
        for row in reader:
            # If the description of the municipality matches
            if row['DESCRIZIONE COMUNE'].strip().lower() == comune_di_nascita.strip().lower():
                return True       
    # If we don't find the municipality
    return False

def validate_sigla_provincia(sprovincia):
    # Open CSV file
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
            
        # We cycle on the lines of the CSV
        for row in reader:
            # If the description of the municipality matches
            if row['SIGLA'].strip().lower() == sprovincia.strip().lower():
                return True       
    # If we don't find the...
    return False

def validate_ddn(value):
    global birth_date

    try:
        #Let's try to convert the entered date
        birth_date = datetime.datetime.strptime(value, "%d/%m/%Y")
        return True
    except ValueError:
        # Let's handle the date format error
        return False

def validate_genere(value):
    if value.upper() == 'M' or value.upper() == 'F':
        return True

    return False

class InfoMessage(BaseModel): #
    cognome: str
    nome: str
    genere: str  
    comune_di_nascita: str
    sigla_provincia: str
    data_di_nascita: str
    
    @field_validator("data_di_nascita")
    @classmethod
    def data_di_nascita_validator(cls, ddn):
        if not validate_ddn(ddn):
            raise ValueError("Il formato della data è errato. Assicurati di usare GG/MM/AAAA (The date format is incorrect. Make sure you use DD/MM/YYYY).")
        now = datetime.datetime.now()
        if birth_date.year > now.year:
            raise ValueError("L'anno di nascita non può essere maggiore dell'anno corrente (The birth year cannot be greater than the current year).")
        return ddn
    
    @field_validator("genere")
    @classmethod
    def genere_validator(cls, gen):
        if not validate_genere(gen):
            raise ValueError("Carattere genere non consentito. Assicurati di usare M o F (Character gender not allowed. Make sure to use M or F).")
        return gen
    
    @field_validator("comune_di_nascita")
    @classmethod
    def comune_validator(cls, comune):
        if not validate_comune(comune):
            raise ValueError(f"Comune (Municipality) '{comune}' non trovato (not found).")
        return comune

    @field_validator("sigla_provincia")
    @classmethod
    def sigla_provincia_validator(cls, sprovincia):
        if not validate_sigla_provincia(sprovincia):
            raise ValueError(f"Provincia (Province) '{sprovincia}' non trovata (not found).")
        return sprovincia

@form #
class MessageForm(CatForm): #
    description = "Calculate the tax code" #
    model_class = InfoMessage #
    start_examples = [ #
        "calcola il codice fiscale",
        "Calculate the tax code",
    ]
    stop_examples = [ #
        "ferma richiesta",
        "stop calculating"
    ]
    ask_confirm = True #
    
    def validate(self, form_data): #
        # Call the default validation
        super().validate(form_data)
        
        # Custom validation logic

        # Add more custom validations as needed
        
        return form_data
       
    def submit(self, form_data): #
        # Calculate the tax code
        if get_cadastral_code(form_data['comune_di_nascita'], form_data['sigla_provincia']):
            tax_id_code = calculate_tax_id_code(form_data["nome"], form_data["cognome"], birth_date, form_data["genere"], land_code)

            # Return a message to the conversation with the order details and estimated time
            return {
                "output": f"Il codice fiscale è (The tax code is): {tax_id_code}"
            }
        else:
            return {
                "output": f"Il Comune (The Municipality) {form_data['comune_di_nascita']} non trovato nella Provincia di (not found in the Province of) {form_data['sigla_provincia']} \n Riprova inserendo i dati corretti...(Try again by entering the correct data...)\n"
            }

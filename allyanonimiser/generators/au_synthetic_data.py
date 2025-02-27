"""
Australian synthetic data generator for PII and insurance-related data.
"""

import os
import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class AustralianSyntheticDataGenerator:
    """
    Generate synthetic Australian PII and insurance-related data for testing.
    
    This generator creates realistic Australian data including:
    - Names, addresses, phone numbers
    - TFNs, Medicare numbers, driver's licenses
    - Insurance policy numbers, claim references
    - Vehicle registrations and VINs
    """
    
    def __init__(self):
        """Initialize the Australian synthetic data generator."""
        # Australian state/territory codes
        self.states = ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]
        
        # Common Australian surnames
        self.surnames = [
            "Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Johnson", 
            "White", "Martin", "Anderson", "Thompson", "Nguyen", "Thomas", "Walker", 
            "Harris", "Lee", "Ryan", "Robinson", "Kelly", "King", "Davis", "Wright", 
            "Green", "Evans", "Young", "Allen", "Hill", "Scott", "Moore", "Mitchell"
        ]
        
        # Common Australian first names
        self.first_names = [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", 
            "Joseph", "Thomas", "Charles", "Mary", "Patricia", "Jennifer", "Linda", 
            "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Oliver", 
            "Jack", "Harry", "Charlie", "Thomas", "Olivia", "Charlotte", "Amelia", 
            "Isla", "Mia", "Ava", "Grace", "Sophia", "Emma"
        ]
        
        # Australian suburbs by state
        self.suburbs = {
            "NSW": ["Sydney", "Newcastle", "Wollongong", "Parramatta", "Penrith", "Gosford", "Campbelltown"],
            "VIC": ["Melbourne", "Geelong", "Ballarat", "Bendigo", "Shepparton", "Melton", "Warrnambool"],
            "QLD": ["Brisbane", "Gold Coast", "Sunshine Coast", "Townsville", "Cairns", "Toowoomba", "Mackay"],
            "SA": ["Adelaide", "Mount Gambier", "Whyalla", "Port Augusta", "Port Lincoln", "Victor Harbor"],
            "WA": ["Perth", "Bunbury", "Geraldton", "Albany", "Kalgoorlie", "Mandurah", "Broome"],
            "TAS": ["Hobart", "Launceston", "Devonport", "Burnie", "Kingston", "Ulverstone", "Sorell"],
            "NT": ["Darwin", "Alice Springs", "Katherine", "Palmerston", "Tennant Creek", "Nhulunbuy"],
            "ACT": ["Canberra", "Belconnen", "Tuggeranong", "Woden", "Gungahlin", "Weston Creek"]
        }
        
        # Common street names
        self.street_names = [
            "High", "Main", "Church", "Park", "George", "Victoria", "King", "Queen",
            "William", "Station", "Bridge", "Albert", "Hill", "River", "Railway",
            "Elizabeth", "Market", "Mill", "North", "South", "East", "West", "Beach",
            "Rose", "Green", "Castle", "James", "York", "John", "Oxford", "New"
        ]
        
        # Street types
        self.street_types = ["Street", "Road", "Avenue", "Drive", "Court", "Place", "Lane", "Way", "Crescent", "Close"]
        
        # Insurance companies
        self.insurance_companies = [
            "Allianz Australia", "QBE Insurance", "AAMI Insurance", "Budget Direct",
            "RACV Insurance", "NRMA Insurance", "Youi Insurance", "Suncorp Insurance",
            "Medibank Insurance", "HCF Insurance", "Bupa Insurance", "CommInsure",
            "Westpac Insurance", "ANZ Insurance", "IAG Insurance", "Apia Insurance"
        ]
        
        # Car makes and models
        self.car_makes_models = {
            "Toyota": ["Corolla", "Camry", "RAV4", "HiLux", "Kluger", "LandCruiser", "Prado"],
            "Mazda": ["CX-5", "CX-3", "Mazda3", "Mazda2", "Mazda6", "BT-50", "MX-5"],
            "Hyundai": ["i30", "Tucson", "Santa Fe", "Kona", "iLoad", "Accent", "Elantra"],
            "Ford": ["Ranger", "Focus", "Escape", "Everest", "Mustang", "Falcon", "Territory"],
            "Holden": ["Commodore", "Colorado", "Astra", "Trax", "Equinox", "Trailblazer", "Acadia"],
            "Mitsubishi": ["Triton", "ASX", "Outlander", "Pajero", "Eclipse Cross", "Mirage", "Lancer"],
            "Kia": ["Cerato", "Sportage", "Sorento", "Rio", "Picanto", "Carnival", "Stinger"],
            "Nissan": ["X-Trail", "Navara", "Qashqai", "Patrol", "Juke", "Pathfinder", "Leaf"]
        }
        
    def generate_australian_name(self) -> str:
        """Generate a random Australian name."""
        first_name = random.choice(self.first_names)
        surname = random.choice(self.surnames)
        return f"{first_name} {surname}"
    
    def generate_australian_address(self) -> str:
        """Generate a random Australian address."""
        house_number = random.randint(1, 300)
        street_name = random.choice(self.street_names)
        street_type = random.choice(self.street_types)
        state = random.choice(self.states)
        suburb = random.choice(self.suburbs[state])
        postcode = self._generate_postcode(state)
        return f"{house_number} {street_name} {street_type}, {suburb} {state} {postcode}"
    
    def _generate_postcode(self, state: str) -> str:
        """Generate a valid Australian postcode for a given state."""
        postcode_ranges = {
            "NSW": (1000, 2999),
            "ACT": (2600, 2618),
            "VIC": (3000, 3999),
            "QLD": (4000, 4999),
            "SA": (5000, 5999),
            "WA": (6000, 6999),
            "TAS": (7000, 7999),
            "NT": (0800, 0899)
        }
        
        if state in postcode_ranges:
            min_val, max_val = postcode_ranges[state]
            return str(random.randint(min_val, max_val))
        
        return "0000"  # Fallback
    
    def generate_australian_phone(self) -> str:
        """Generate a random Australian phone number."""
        formats = [
            "04## ### ###",  # Mobile
            "02 #### ####",  # NSW/ACT landline
            "03 #### ####",  # VIC/TAS landline
            "07 #### ####",  # QLD landline
            "08 #### ####"   # SA/WA/NT landline
        ]
        
        format_template = random.choice(formats)
        phone_number = ""
        
        for char in format_template:
            if char == "#":
                phone_number += str(random.randint(0, 9))
            else:
                phone_number += char
                
        return phone_number
    
    def generate_tfn(self) -> str:
        """Generate a valid Australian Tax File Number (TFN)."""
        # TFNs are 8 or 9 digits
        # Using the weighted sum algorithm for validation
        weights = [1, 4, 3, 7, 5, 8, 6, 9, 10]
        
        # Generate 8 random digits
        digits = [random.randint(0, 9) for _ in range(8)]
        
        # Calculate weighted sum
        weighted_sum = sum(w * d for w, d in zip(weights, digits))
        
        # Calculate check digit
        remainder = weighted_sum % 11
        if remainder == 0:
            digits.append(0)
        else:
            digits.append(11 - remainder)
        
        # Format as xxx xxx xxx
        tfn = ''.join(str(d) for d in digits)
        return f"{tfn[:3]} {tfn[3:6]} {tfn[6:]}"
    
    def generate_medicare_number(self) -> str:
        """Generate a valid Australian Medicare number."""
        # Medicare numbers are 10 digits
        # 8 digits + 1 check digit + 1 issue number
        
        # Generate 8 random digits
        digits = [random.randint(0, 9) for _ in range(8)]
        
        # Calculate check digit using Luhn algorithm
        def luhn_check(digits):
            # Double every second digit from right to left
            doubled = [(2 * d) if i % 2 == 0 else d for i, d in enumerate(reversed(digits))]
            # Sum all digits (if doubled > 9, sum its digits)
            total = sum(d // 10 + d % 10 if d > 9 else d for d in doubled)
            # Check digit is the amount needed to reach the next multiple of 10
            return (10 - (total % 10)) % 10
        
        check_digit = luhn_check(digits)
        
        # Add check digit and issue number (1-5)
        digits.append(check_digit)
        digits.append(random.randint(1, 5))
        
        # Format as #### #####-#
        medicare = ''.join(str(d) for d in digits)
        return f"{medicare[:4]} {medicare[4:9]}-{medicare[9]}"
    
    def generate_drivers_license(self, state: Optional[str] = None) -> str:
        """Generate an Australian driver's license number for a specified state."""
        if state is None:
            state = random.choice(self.states)
            
        # Different formats by state
        formats = {
            "NSW": lambda: str(random.randint(10000000, 99999999)),  # 8 digits
            "VIC": lambda: ''.join(str(random.randint(0, 9)) for _ in range(9)),  # 9 digits
            "QLD": lambda: ''.join(str(random.randint(0, 9)) for _ in range(9)),  # 9 digits
            "SA": lambda: 'S' + ''.join(str(random.randint(0, 9)) for _ in range(8)),  # S + 8 digits
            "WA": lambda: ''.join(str(random.randint(0, 9)) for _ in range(7)),  # 7 digits
            "TAS": lambda: ''.join(str(random.randint(0, 9)) for _ in range(9)),  # 9 digits
            "NT": lambda: ''.join(str(random.randint(0, 9)) for _ in range(6)),  # 6 digits
            "ACT": lambda: ''.join(str(random.randint(0, 9)) for _ in range(8))  # 8 digits
        }
        
        license_number = formats.get(state, lambda: "000000")()
        return f"{state}{license_number}"
    
    def generate_bsb_account(self) -> str:
        """Generate a valid Australian BSB and account number."""
        # BSB format: xxx-xxx
        bsb = f"{random.randint(100, 999)}-{random.randint(100, 999)}"
        
        # Account numbers are typically 6-10 digits
        account_length = random.randint(6, 10)
        account = ''.join(str(random.randint(0, 9)) for _ in range(account_length))
        
        return f"BSB: {bsb}, Account: {account}"
    
    def generate_policy_number(self) -> str:
        """Generate an insurance policy number."""
        formats = [
            "POL-######",
            "P#######",
            "INS######",
            "POL######",
            "P-######-##"
        ]
        
        format_template = random.choice(formats)
        policy_number = ""
        
        for char in format_template:
            if char == "#":
                policy_number += str(random.randint(0, 9))
            else:
                policy_number += char
                
        return policy_number
    
    def generate_claim_number(self) -> str:
        """Generate an insurance claim reference number."""
        formats = [
            "CL-#######",
            "C#######",
            "CLM######",
            "CLM-######",
            "CL######"
        ]
        
        format_template = random.choice(formats)
        claim_number = ""
        
        for char in format_template:
            if char == "#":
                claim_number += str(random.randint(0, 9))
            else:
                claim_number += char
                
        return claim_number
    
    def generate_vehicle_registration(self, state: Optional[str] = None) -> str:
        """Generate an Australian vehicle registration number."""
        if state is None:
            state = random.choice(self.states)
            
        # Different formats by state
        formats = {
            "NSW": ["### ###", "## ## ##"],  # NSW format
            "VIC": ["### ###", "### ###", "# ### ##"],  # VIC format
            "QLD": ["### ###", "### ###"],  # QLD format
            "SA": ["S### ###", "#### ###"],  # SA format
            "WA": ["#@@ ###", "### ###"],  # WA format (# = digit, @ = letter)
            "TAS": ["@## ###", "@### ##"],  # TAS format
            "NT": ["## ##@", "### ###"],  # NT format
            "ACT": ["@@@ ###", "@## ###"]  # ACT format
        }
        
        format_template = random.choice(formats.get(state, ["### ###"]))
        rego = ""
        
        for char in format_template:
            if char == "#":
                rego += str(random.randint(0, 9))
            elif char == "@":
                rego += random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")  # Skip I and O as they look like numbers
            else:
                rego += char
                
        return rego
    
    def generate_vin(self) -> str:
        """Generate a valid Vehicle Identification Number (VIN)."""
        # VINs are 17 characters
        # Characters allowed: 0-9, A-Z excluding I, O, Q
        allowed_chars = "0123456789ABCDEFGHJKLMNPRSTUVWXYZ"
        
        # Generate a random VIN
        vin = ''.join(random.choice(allowed_chars) for _ in range(17))
        
        return vin
    
    def generate_person(self) -> Dict[str, str]:
        """Generate a complete person profile with Australian PII."""
        state = random.choice(self.states)
        
        return {
            "name": self.generate_australian_name(),
            "address": self.generate_australian_address(),
            "phone": self.generate_australian_phone(),
            "tfn": self.generate_tfn(),
            "medicare": self.generate_medicare_number(),
            "drivers_license": self.generate_drivers_license(state),
            "bsb_account": self.generate_bsb_account(),
            "email": self._generate_email()
        }
    
    def _generate_email(self) -> str:
        """Generate a random email address."""
        domains = ["gmail.com", "outlook.com", "yahoo.com.au", "hotmail.com", "iinet.net.au", "bigpond.com"]
        
        first_name = random.choice(self.first_names).lower()
        surname = random.choice(self.surnames).lower()
        
        formats = [
            f"{first_name}.{surname}@{random.choice(domains)}",
            f"{first_name}{surname}@{random.choice(domains)}",
            f"{first_name}.{surname}{random.randint(1, 99)}@{random.choice(domains)}",
            f"{first_name[0]}{surname}@{random.choice(domains)}",
            f"{surname}.{first_name}@{random.choice(domains)}"
        ]
        
        return random.choice(formats)
    
    def generate_insurance_claim(self) -> Dict[str, Any]:
        """Generate a synthetic insurance claim with details."""
        person = self.generate_person()
        
        # Select car make and model
        car_make = random.choice(list(self.car_makes_models.keys()))
        car_model = random.choice(self.car_makes_models[car_make])
        
        # Generate claim details
        claim_date = datetime.now() - timedelta(days=random.randint(1, 365))
        claim_date_str = claim_date.strftime("%d/%m/%Y")
        
        claim_types = ["Motor Vehicle", "Home & Contents", "Health", "Travel", "Business", "Personal Liability"]
        claim_type = random.choice(claim_types)
        
        claim_status = random.choice(["Open", "Pending", "Approved", "Settled", "Denied", "Under Review"])
        
        claim = {
            "customer": person,
            "policy_number": self.generate_policy_number(),
            "claim_number": self.generate_claim_number(),
            "claim_date": claim_date_str,
            "claim_type": claim_type,
            "claim_status": claim_status,
            "insurer": random.choice(self.insurance_companies)
        }
        
        # Add type-specific details
        if claim_type == "Motor Vehicle":
            claim["vehicle"] = {
                "make": car_make,
                "model": car_model,
                "year": random.randint(2000, 2023),
                "registration": self.generate_vehicle_registration(),
                "vin": self.generate_vin()
            }
            
            incident_types = ["Collision", "Theft", "Vandalism", "Weather Damage", "Fire", "Single Vehicle Accident"]
            claim["incident_type"] = random.choice(incident_types)
            claim["damage_amount"] = f"${random.randint(500, 15000):,}"
            
        elif claim_type == "Home & Contents":
            incident_types = ["Theft", "Fire", "Flood", "Storm Damage", "Burst Pipe", "Vandalism", "Malicious Damage"]
            claim["incident_type"] = random.choice(incident_types)
            claim["property_address"] = self.generate_australian_address()
            claim["damage_amount"] = f"${random.randint(1000, 50000):,}"
            
        # Generate a claim description
        claim["description"] = self._generate_claim_description(claim)
        
        return claim
    
    def _generate_claim_description(self, claim: Dict[str, Any]) -> str:
        """Generate a realistic description for a claim."""
        claim_type = claim["claim_type"]
        
        if claim_type == "Motor Vehicle":
            vehicle = claim["vehicle"]
            incident_type = claim["incident_type"]
            
            descriptions = [
                f"Customer reported a {incident_type.lower()} involving their {vehicle['year']} {vehicle['make']} {vehicle['model']} (Registration: {vehicle['registration']}). The incident occurred on {claim['claim_date']}.",
                f"Claim relates to {incident_type.lower()} damage to insured's {vehicle['year']} {vehicle['make']} {vehicle['model']}. Vehicle was parked at shopping center when incident occurred.",
                f"{incident_type} occurred at intersection. Insured's {vehicle['make']} {vehicle['model']} was hit by another vehicle. Police report filed.",
                f"Customer's {vehicle['make']} {vehicle['model']} sustained damage due to {incident_type.lower()}. Initial assessment estimates repairs at {claim['damage_amount']}.",
                f"{incident_type} involving insured's {vehicle['year']} {vehicle['make']} {vehicle['model']}. Customer has requested a hire car while vehicle is being repaired."
            ]
            
        elif claim_type == "Home & Contents":
            incident_type = claim["incident_type"]
            
            descriptions = [
                f"Customer reported {incident_type.lower()} at their property located at {claim['property_address']}. Incident occurred on {claim['claim_date']}.",
                f"{incident_type} caused significant damage to customer's property. Initial assessment estimates repairs at {claim['damage_amount']}.",
                f"Claim relates to {incident_type.lower()} damage to insured's home. Customer has temporarily relocated while repairs are completed.",
                f"Customer's property sustained damage due to {incident_type.lower()}. Building assessor has been assigned to evaluate the full extent of damage.",
                f"{incident_type} at insured's property resulted in damage to both building and contents. Detailed inventory of damaged items is being prepared."
            ]
            
        else:
            descriptions = [
                f"Customer filed a {claim_type} claim on {claim['claim_date']}. Claim is currently {claim['claim_status'].lower()}.",
                f"{claim_type} claim submitted by insured. Further documentation has been requested to process the claim.",
                f"Claim relates to a {claim_type.lower()} incident. Customer has provided all required documentation.",
                f"Customer initiated a {claim_type} claim. Assessment is underway to determine coverage under their policy {claim['policy_number']}.",
                f"{claim_type} claim is being processed. Initial review indicates the claim is within policy coverage limits."
            ]
            
        return random.choice(descriptions)
    
    def generate_dataset(self, num_documents: int = 100, output_dir: str = "au_synthetic_dataset", include_annotations: bool = True) -> None:
        """
        Generate a dataset of Australian insurance documents with PII.
        
        Args:
            num_documents: Number of documents to generate
            output_dir: Directory to save the dataset
            include_annotations: Whether to include PII annotations
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate documents
        documents = []
        
        for i in range(num_documents):
            # Generate a claim
            claim = self.generate_insurance_claim()
            
            # Create a document from the claim
            document = {
                "id": f"doc-{i+1:04d}",
                "type": claim["claim_type"],
                "text": self._generate_document_text(claim),
                "metadata": {
                    "claim_number": claim["claim_number"],
                    "policy_number": claim["policy_number"],
                    "claim_date": claim["claim_date"],
                    "claim_status": claim["claim_status"],
                    "insurer": claim["insurer"]
                }
            }
            
            # Add annotations if requested
            if include_annotations:
                document["annotations"] = self._generate_annotations(document["text"], claim)
            
            documents.append(document)
            
            # Save individual document
            with open(os.path.join(output_dir, f"document_{i+1:04d}.json"), "w") as f:
                json.dump(document, f, indent=2)
        
        # Save dataset index
        with open(os.path.join(output_dir, "dataset_index.json"), "w") as f:
            json.dump({
                "dataset_name": "Australian Insurance Synthetic Dataset",
                "num_documents": num_documents,
                "generation_date": datetime.now().strftime("%Y-%m-%d"),
                "documents": [{"id": doc["id"], "type": doc["type"]} for doc in documents]
            }, f, indent=2)
        
        print(f"Generated {num_documents} documents in {output_dir}")
    
    def _generate_document_text(self, claim: Dict[str, Any]) -> str:
        """Generate document text from claim information."""
        customer = claim["customer"]
        
        # Create document sections
        header = f"""
{claim['insurer']}
CLAIM REFERENCE: {claim['claim_number']}
POLICY NUMBER: {claim['policy_number']}
DATE: {claim['claim_date']}
STATUS: {claim['claim_status']}
        """
        
        customer_section = f"""
CUSTOMER DETAILS:
Name: {customer['name']}
Address: {customer['address']}
Phone: {customer['phone']}
Email: {customer['email']}
        """
        
        claim_section = f"""
CLAIM DETAILS:
Type: {claim['claim_type']}
Date of Incident: {claim['claim_date']}
Description: {claim['description']}
        """
        
        # Add type-specific sections
        additional_sections = ""
        
        if claim['claim_type'] == "Motor Vehicle":
            vehicle = claim['vehicle']
            additional_sections += f"""
VEHICLE DETAILS:
Make: {vehicle['make']}
Model: {vehicle['model']}
Year: {vehicle['year']}
Registration: {vehicle['registration']}
VIN: {vehicle['vin']}
            """
            
        elif claim['claim_type'] == "Home & Contents":
            additional_sections += f"""
PROPERTY DETAILS:
Address: {claim['property_address']}
Incident Type: {claim['incident_type']}
Estimated Damage: {claim['damage_amount']}
            """
        
        # Sometimes include sensitive information
        if random.random() < 0.3:
            additional_sections += f"""
ADDITIONAL INFORMATION:
TFN: {customer['tfn']}
Medicare: {customer['medicare']}
Driver's License: {customer['drivers_license']}
Bank Details: {customer['bsb_account']}
            """
        
        notes_section = f"""
CLAIM NOTES:
{datetime.now().strftime('%d/%m/%Y')} - Claim registered in system
{(datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')} - Initial assessment completed
{(datetime.now() - timedelta(days=2)).strftime('%d/%m/%Y')} - Customer contacted to confirm details
{(datetime.now() - timedelta(days=3)).strftime('%d/%m/%Y')} - Documentation received from customer

ACTIONS:
1. Complete assessment by {(datetime.now() + timedelta(days=5)).strftime('%d/%m/%Y')}
2. Contact repair shop for quote
3. Schedule follow-up call with customer
        """
        
        # Combine all sections
        document_text = header + customer_section + claim_section + additional_sections + notes_section
        
        return document_text
    
    def _generate_annotations(self, text: str, claim: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate PII annotations for the document text."""
        annotations = []
        customer = claim["customer"]
        
        # Define patterns to find
        patterns = {
            "PERSON": customer["name"],
            "AU_ADDRESS": customer["address"],
            "AU_PHONE": customer["phone"],
            "EMAIL_ADDRESS": customer["email"],
            "AU_TFN": customer["tfn"],
            "AU_MEDICARE": customer["medicare"],
            "AU_DRIVERS_LICENSE": customer["drivers_license"],
            "AU_BSB_ACCOUNT": customer["bsb_account"],
            "POLICY_NUMBER": claim["policy_number"],
            "CLAIM_NUMBER": claim["claim_number"]
        }
        
        # Add vehicle details if available
        if "vehicle" in claim:
            patterns["VEHICLE_REGISTRATION"] = claim["vehicle"]["registration"]
            patterns["VEHICLE_VIN"] = claim["vehicle"]["vin"]
        
        # Find and annotate patterns
        for entity_type, value in patterns.items():
            # Find all occurrences
            start_idx = 0
            while start_idx < len(text):
                idx = text.find(value, start_idx)
                if idx == -1:
                    break
                    
                annotations.append({
                    "entity_type": entity_type,
                    "start": idx,
                    "end": idx + len(value),
                    "text": value
                })
                
                start_idx = idx + 1
        
        return annotations
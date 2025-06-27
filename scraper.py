import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from tqdm import tqdm
import google.generativeai as genai
import datetime
from tavily import TavilyClient
import json
import ast
import logging
from urllib.parse import urlparse

# Setup Gemini API - Replace with your API key
genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")
model = genai.GenerativeModel("gemini-1.5-flash")

# Setup Tavily API - Replace with your API key
tavily_client = TavilyClient(api_key="YOUR_TAVILY_API_KEY_HERE")

# Setup SERP API - Replace with your API key
SERP_API_KEY = "YOUR_SERP_API_KEY_HERE"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_url_accessible(url):
    """
    Check if a URL is accessible and valid
    """
    if not url or url.lower() in ['blank', 'n/a', 'not found', '']:
        return False
    
    try:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parse URL to check if it's valid
        parsed = urlparse(url)
        if not parsed.netloc:
            return False
        
        # Make request with timeout
        response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        return response.status_code < 400
    except:
        return False

def validate_email(email):
    """
    Validate email format
    """
    if not email or email.lower() in ['blank', 'n/a', 'not found', '']:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_phone(phone):
    """
    Validate Indian phone number format
    """
    if not phone or phone.lower() in ['blank', 'n/a', 'not found', '']:
        return False
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid Indian number (10 digits or 10 digits with country code)
    if len(digits) == 10 or (len(digits) == 12 and digits.startswith('91')):
        return True
    
    return False

def get_company_details_from_gemini(company, industry, location):
    prompt = f"""
    You are an expert internet researcher. Search the web comprehensively to find information about this EXACT company:

    TARGET COMPANY:
    Company Name: "{company}"
    Business Type: {industry}
    Location: {location}

    COMPREHENSIVE SEARCH STRATEGY - Use ALL these search methods:

    1. BASIC SEARCHES:
    - "{company}"
    - "{company}" {location}
    - "{company}" {industry}
    - "{company}" {industry} {location}
    - {company} contact details
    - {company} phone number
    - {company} email address

    2. BUSINESS DIRECTORY SEARCHES:
    - "{company}" site:justdial.com
    - "{company}" site:indiamart.com
    - "{company}" site:tradeindia.com
    - "{company}" site:sulekha.com
    - "{company}" site:yellowpages.co.in
    - "{company}" site:google.com/maps
    - "{company}" {location} justdial
    - "{company}" {location} indiamart
    - "{company}" {location} business directory

    3. SOCIAL MEDIA SEARCHES:
    - "{company}" site:facebook.com
    - "{company}" site:instagram.com
    - "{company}" site:linkedin.com
    - "{company}" facebook page
    - "{company}" instagram profile
    - "{company}" linkedin company

    4. CONTACT SEARCHES:
    - "{company}" contact us
    - "{company}" address phone
    - "{company}" email contact
    - "{company}" {location} contact
    - "{company}" owner director
    - "{company}" proprietor

    5. WEBSITE SEARCHES:
    - "{company}" official website
    - "{company}" .com
    - "{company}" .in
    - "{company}" .co.in
    - site:{company.lower().replace(' ', '')}.com
    - site:{company.lower().replace(' ', '')}.in

    VALIDATION REQUIREMENTS:
    - Company name must match "{company}" (exact or very close spelling)
    - Industry/business type should be "{industry}" or related
    - Location should be "{location}" or nearby areas
    - Cross-verify information from multiple sources

    WHAT TO EXTRACT:
    - Official website URL (check multiple domains)
    - Business email addresses (info@, contact@, admin@, sales@)
    - Phone numbers (mobile, landline, WhatsApp Business)
    - Complete business address with pincode
    - Facebook page URL
    - Instagram profile URL
    - LinkedIn company page URL
    - Owner/Proprietor/Director names
    - Year of establishment (if available)

    SEARCH LIKE A HUMAN:
    - Try different keyword combinations
    - Check business listings thoroughly
    - Look for contact pages on websites
    - Search for company reviews and mentions
    - Check government business registrations
    - Look for trade associations and memberships

    OUTPUT FORMAT:
    Website: [Full URL or BLANK]
    Email: [Email address or BLANK]
    Phone: [Phone number or BLANK]
    Facebook: [Facebook URL or BLANK]
    Instagram: [Instagram URL or BLANK]
    LinkedIn: [LinkedIn URL or BLANK]
    Owner(s): [Name(s) or BLANK]
    Address: [Complete address or BLANK]
    Match_Type: [EXACT/PARTIAL/NOT_FOUND]
    Confidence: [HIGH/MEDIUM/LOW]

    CRITICAL INSTRUCTIONS:
    - Search extensively using ALL the above methods
    - Provide REAL data only, no placeholder text
    - If you find the company on JustDial, extract ALL available information
    - Cross-reference data from multiple sources for accuracy
    - Include phone numbers, addresses, and contact details from business directories
    - Better to provide verified data than guess
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

def get_internal_links(soup, base_url):
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if any(word in href.lower() for word in ['contact', 'about', 'team']):
            full_url = requests.compat.urljoin(base_url, href)
            links.add(full_url)
    return links

def extract_social_links(soup):
    social_links = {"Facebook": "", "Instagram": "", "LinkedIn": ""}
    for a in soup.find_all("a", href=True):
        href = a['href']
        if "facebook.com" in href:
            social_links["Facebook"] = href
        elif "instagram.com" in href:
            social_links["Instagram"] = href
        elif "linkedin.com" in href:
            social_links["LinkedIn"] = href
    return social_links

def clean_contacts(emails, phones):
    unique_emails = list(set([e.lower() for e in emails if '@' in e and '.' in e]))
    
    # Improved phone cleaning
    cleaned_phones = []
    for phone in phones:
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # If number has country code, remove it (assuming +91 or similar)
        if len(digits) > 10:
            digits = digits[-10:]
            
        # Only keep valid 10-digit numbers
        if len(digits) == 10:
            # Format as XXXXX XXXXX
            formatted = f"{digits[:5]} {digits[5:]}"
            cleaned_phones.append(formatted)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_phones = []
    for phone in cleaned_phones:
        if phone not in seen:
            seen.add(phone)
            unique_phones.append(phone)
            
    return unique_emails, unique_phones

def search_with_tavily(company, industry, location):
    """
    Use Tavily to search the internet comprehensively for company information
    """
    try:
        # Comprehensive search queries like a human would use on Google
        search_queries = [
            # Basic company searches
            f'"{company}"',
            f'"{company}" {location}',
            f'"{company}" {industry}',
            f'"{company}" {industry} {location}',
            
            # Contact information searches
            f'"{company}" contact details',
            f'"{company}" phone number',
            f'"{company}" email address',
            f'"{company}" {location} contact',
            f'"{company}" address phone',
            
            # Business directory searches
            f'"{company}" justdial',
            f'"{company}" indiamart',
            f'"{company}" {location} justdial',
            f'"{company}" {location} indiamart',
            f'"{company}" {location} business directory',
            f'"{company}" yellowpages',
            f'"{company}" sulekha',
            
            # Website searches
            f'"{company}" official website',
            f'"{company}" website',
            f'"{company}" .com',
            f'"{company}" .in',
            
            # Social media searches
            f'"{company}" facebook',
            f'"{company}" instagram',
            f'"{company}" linkedin',
            f'"{company}" social media',
            
            # Owner/business searches
            f'"{company}" owner',
            f'"{company}" proprietor',
            f'"{company}" director',
            f'"{company}" {location} owner'
        ]
        
        all_results = []
        
        # Process searches in batches to avoid overwhelming the API
        for i, query in enumerate(search_queries):
            try:
                print(f"  🔍 Tavily searching ({i+1}/{len(search_queries)}): {query}")
                response = tavily_client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=3,
                    include_domains=[
                        "justdial.com", "indiamart.com", "sulekha.com", 
                        "yellowpages.co.in", "tradeindia.com", "exportersindia.com",
                        "facebook.com", "instagram.com", "linkedin.com",
                        "google.com", "maps.google.com"
                    ],
                    include_answer=True
                )
                
                if response and 'results' in response:
                    all_results.extend(response['results'])
                    
                # Limit to first 15 queries to avoid too many API calls
                if i >= 14:
                    break
                    
            except Exception as e:
                print(f"    ❌ Tavily query failed: {e}")
                continue
        
        if not all_results:
            return None
            
        # Extract information from search results
        extracted_info = {
            "website": "",
            "email": "",
            "phone": "",
            "facebook": "",
            "instagram": "",
            "linkedin": "",
            "owner": "",
            "address": ""
        }
        
        # Combine all content for analysis and validate company relevance
        combined_content = ""
        company_keywords = company.lower().split()
        industry_keywords = industry.lower().split()
        location_keywords = location.lower().split()
        
        for result in all_results:
            # Check if result is relevant to our target company
            result_text = ""
            if 'content' in result:
                result_text += result['content'].lower()
            if 'title' in result:
                result_text += result['title'].lower()
            if 'url' in result:
                result_text += result['url'].lower()
            
            # Validate if this result is about our target company
            company_match = any(keyword in result_text for keyword in company_keywords)
            location_match = any(keyword in result_text for keyword in location_keywords)
            
            # More flexible matching - require company name and either industry or location
            industry_match = any(keyword in result_text for keyword in industry_keywords)
            
            # Include results that mention company name + (industry OR location)
            if company_match and (industry_match or location_match):
                if 'content' in result:
                    combined_content += result['content'] + "\n"
                if 'title' in result:
                    combined_content += result['title'] + "\n"
                
                if 'url' in result:
                    # Extract social media URLs directly (only if relevant to our company)
                    url = result['url']
                    if 'facebook.com' in url and not extracted_info["facebook"]:
                        # Additional validation for social media
                        if any(keyword in url.lower() for keyword in company_keywords):
                            extracted_info["facebook"] = url
                    elif 'instagram.com' in url and not extracted_info["instagram"]:
                        if any(keyword in url.lower() for keyword in company_keywords):
                            extracted_info["instagram"] = url
                    elif 'linkedin.com' in url and not extracted_info["linkedin"]:
                        if any(keyword in url.lower() for keyword in company_keywords):
                            extracted_info["linkedin"] = url
                    elif not extracted_info["website"] and any(domain in url for domain in ['.com', '.in', '.co.in', '.org']):
                        if 'facebook' not in url and 'instagram' not in url and 'linkedin' not in url:
                            if any(keyword in url.lower() for keyword in company_keywords):
                                extracted_info["website"] = url
        
        # Use regex to extract emails and phones from content
        if combined_content:
            # Extract emails - multiple patterns
            email_patterns = [
                r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
                r'Email[:\s]+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',
                r'E-mail[:\s]+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',
                r'Contact[:\s]+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
            ]
            
            for pattern in email_patterns:
                emails = re.findall(pattern, combined_content, re.IGNORECASE)
                if emails:
                    extracted_info["email"] = emails[0] if isinstance(emails[0], str) else emails[0]
                    break
            
            # Extract phone numbers - comprehensive patterns
            phone_patterns = [
                r'(?:\+91[-.\s]?)?\d{5}[-.\s]?\d{5}',  # Indian format: 12345 67890
                r'(?:\+91[-.\s]?)?\d{10}',             # 10 digits
                r'(?:\+91[-.\s]?)?\d{4}[-.\s]?\d{3}[-.\s]?\d{3}',  # 1234 567 890
                r'(?:\+91[-.\s]?)?\(\d{3,4}\)[-.\s]?\d{3}[-.\s]?\d{3,4}',  # (123) 456 7890
                r'Phone[:\s]+(?:\+91[-.\s]?)?\d{10}',  # Phone: 1234567890
                r'Mobile[:\s]+(?:\+91[-.\s]?)?\d{10}', # Mobile: 1234567890
                r'Contact[:\s]+(?:\+91[-.\s]?)?\d{10}' # Contact: 1234567890
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, combined_content, re.IGNORECASE)
                if phones:
                    phone = phones[0].strip()
                    # Clean up the phone number
                    phone = re.sub(r'[^\d+]', '', phone)
                    if len(phone) >= 10:
                        extracted_info["phone"] = phone
                        break
            
            # Extract address information
            address_patterns = [
                r'Address[:\s]+([^,\n]+(?:,[^,\n]+)*)',
                r'Location[:\s]+([^,\n]+(?:,[^,\n]+)*)',
                r'Office[:\s]+([^,\n]+(?:,[^,\n]+)*)'
            ]
            
            for pattern in address_patterns:
                addresses = re.findall(pattern, combined_content, re.IGNORECASE)
                if addresses:
                    extracted_info["address"] = addresses[0].strip()
                    break
        
        # Format results
        if any(extracted_info.values()):
            result_text = f"""
Website: {extracted_info['website']}
Email: {extracted_info['email']}
Phone: {extracted_info['phone']}
Facebook: {extracted_info['facebook']}
Instagram: {extracted_info['instagram']}
LinkedIn: {extracted_info['linkedin']}
Owner(s): {extracted_info['owner']}
Address: {extracted_info['address']}
Match_Type: TAVILY_SEARCH
Confidence: MEDIUM
"""
            return result_text.strip()
        
        return None
        
    except Exception as e:
        print(f"    ❌ Tavily search error: {e}")
        return None

def search_with_serp_api(company, industry, location):
    """
    Use SERP API to search Google for company information
    """
    try:
        print(f"  🔍 SERP API searching Google for: {company}")
        
        # Construct search query
        search_query = f'"{company}" {industry} {location} contact phone email'
        
        # SERP API endpoint
        url = "https://serpapi.com/search"
        params = {
            'api_key': SERP_API_KEY,
            'engine': 'google',
            'q': search_query,
            'num': 10,
            'gl': 'in',  # India
            'hl': 'en'   # English
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract information from search results
            extracted_info = {
                "website": "",
                "email": "",
                "phone": "",
                "facebook": "",
                "instagram": "",
                "linkedin": "",
                "owner": "",
                "address": "",
                "raw_results": []
            }
            
            # Process organic results
            if 'organic_results' in data:
                for result in data['organic_results']:
                    result_info = {
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'snippet': result.get('snippet', ''),
                        'displayed_link': result.get('displayed_link', '')
                    }
                    extracted_info['raw_results'].append(result_info)
                    
                    # Extract website
                    if not extracted_info['website']:
                        link = result.get('link', '')
                        if any(domain in link for domain in ['.com', '.in', '.co.in', '.org']):
                            if not any(social in link for social in ['facebook', 'instagram', 'linkedin', 'twitter']):
                                extracted_info['website'] = link
                    
                    # Extract social media links
                    link = result.get('link', '')
                    if 'facebook.com' in link and not extracted_info['facebook']:
                        extracted_info['facebook'] = link
                    elif 'instagram.com' in link and not extracted_info['instagram']:
                        extracted_info['instagram'] = link
                    elif 'linkedin.com' in link and not extracted_info['linkedin']:
                        extracted_info['linkedin'] = link
                    
                    # Extract emails and phones from snippets
                    snippet = result.get('snippet', '')
                    if snippet:
                        # Email extraction
                        if not extracted_info['email']:
                            emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', snippet)
                            if emails:
                                extracted_info['email'] = emails[0]
                        
                        # Phone extraction
                        if not extracted_info['phone']:
                            phones = re.findall(r'(?:\+91[-.\s]?)?\d{5}[-.\s]?\d{5}', snippet)
                            if phones:
                                extracted_info['phone'] = phones[0]
            
            # Process knowledge graph if available
            if 'knowledge_graph' in data:
                kg = data['knowledge_graph']
                if not extracted_info['website'] and 'website' in kg:
                    extracted_info['website'] = kg['website']
                if not extracted_info['phone'] and 'phone' in kg:
                    extracted_info['phone'] = kg['phone']
                if not extracted_info['address'] and 'address' in kg:
                    extracted_info['address'] = kg['address']
            
            return extracted_info
        else:
            print(f"    ❌ SERP API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"    ❌ SERP API search error: {e}")
        return None

def refine_data_with_gemini(company, industry, location, gemini_data, tavily_data, serp_data):
    """
    Use Gemini to analyze and refine all collected data sources
    """
    try:
        # Prepare data summary for Gemini
        data_summary = f"""
        COMPANY: {company}
        INDUSTRY: {industry}
        LOCATION: {location}
        
        DATA SOURCE 1 - GEMINI AI:
        {gemini_data if gemini_data else "No data found"}
        
        DATA SOURCE 2 - TAVILY SEARCH:
        {tavily_data if tavily_data else "No data found"}
        
        DATA SOURCE 3 - SERP API RESULTS:
        {json.dumps(serp_data, indent=2) if serp_data else "No data found"}
        """
        
        prompt = f"""
        You are a data validation expert. Analyze the following company information collected from multiple sources and provide the MOST ACCURATE and RELIABLE data.

        {data_summary}

        VALIDATION RULES:
        1. Company name must match "{company}" exactly or very closely
        2. Industry must be "{industry}" or closely related
        3. Location must be "{location}" or nearby areas
        4. Cross-reference data from all sources
        5. Choose the most reliable and consistent information
        6. Verify email formats are valid
        7. Verify phone numbers are Indian format
        8. Verify URLs are accessible and relevant

        QUALITY CHECKS:
        - If multiple sources provide same data, it's more reliable
        - Prefer official websites over social media for contact info
        - Prefer business directories (JustDial, IndiaMART) for phone/address
        - Validate email domains match company names when possible
        - Ensure social media profiles belong to the correct company

                 OUTPUT FORMAT - RESPOND ONLY WITH VALID JSON:
         {{
           "Website": "https://example.com or BLANK",
           "Email": "info@example.com or BLANK", 
           "Phone": "+91 98765 43210 or BLANK",
           "Facebook": "https://facebook.com/company or BLANK",
           "Instagram": "https://instagram.com/company or BLANK", 
           "LinkedIn": "https://linkedin.com/company/company or BLANK",
           "Owner": "Owner Name or BLANK",
           "Address": "Complete Address or BLANK",
           "Data_Quality": "EXCELLENT/GOOD/FAIR/POOR",
           "Sources_Used": "List of sources used",
           "Confidence_Score": "1-10 scale",
           "Validation_Notes": "Brief notes on data reliability"
         }}

         CRITICAL INSTRUCTIONS:
         - RESPOND ONLY WITH VALID JSON - NO OTHER TEXT
         - Only provide data you are confident belongs to "{company}" in "{industry}"
         - If sources conflict, choose the most authoritative source
         - If data quality is poor or unreliable, mark fields as "BLANK"
         - Provide reasoning for data quality assessment
         - Better to have "BLANK" than incorrect data
         """
         
        response = model.generate_content(prompt)
        return response.text
         
    except Exception as e:
        logger.error(f"Gemini refinement error for {company}: {e}")
        return None

def process_refined_data(company, industry, location, refined_result):
    """
    Process and validate refined data with smart priority matrix
    """
    try:
        # Try to parse JSON response
        if refined_result:
            # Clean the response (remove any markdown formatting)
            clean_result = refined_result.strip()
            if clean_result.startswith('```json'):
                clean_result = clean_result[7:]
            if clean_result.endswith('```'):
                clean_result = clean_result[:-3]
            clean_result = clean_result.strip()
            
            # Parse JSON
            try:
                data_dict = json.loads(clean_result)
            except json.JSONDecodeError:
                # Fallback to ast.literal_eval
                try:
                    data_dict = ast.literal_eval(clean_result)
                except:
                    logger.error(f"Failed to parse JSON for {company}: {clean_result[:200]}...")
                    # Log the failure
                    with open("gemini_failures.log", "a", encoding="utf-8") as log:
                        log.write(f"\n{'='*50}\n")
                        log.write(f"Company: {company}\n")
                        log.write(f"Industry: {industry}\n") 
                        log.write(f"Location: {location}\n")
                        log.write(f"Raw Gemini Output:\n{refined_result}\n")
                        log.write(f"{'='*50}\n")
                    return None
            
            # Validate and clean data
            validated_data = {}
            
            # Website validation
            website = data_dict.get("Website", "").strip()
            if website and website != "BLANK":
                if is_url_accessible(website):
                    validated_data["Website"] = website
                    logger.info(f"✅ Valid website found for {company}: {website}")
                else:
                    logger.warning(f"⚠️ Website not accessible for {company}: {website}")
            
            # Email validation
            email = data_dict.get("Email", "").strip()
            if email and email != "BLANK":
                if validate_email(email):
                    validated_data["Email"] = email
                    logger.info(f"✅ Valid email found for {company}: {email}")
                else:
                    logger.warning(f"⚠️ Invalid email format for {company}: {email}")
            
            # Phone validation
            phone = data_dict.get("Phone", "").strip()
            if phone and phone != "BLANK":
                if validate_phone(phone):
                    validated_data["Phone"] = phone
                    logger.info(f"✅ Valid phone found for {company}: {phone}")
                else:
                    logger.warning(f"⚠️ Invalid phone format for {company}: {phone}")
            
            # Social media validation (basic URL check)
            for social in ["Facebook", "Instagram", "LinkedIn"]:
                social_url = data_dict.get(social, "").strip()
                if social_url and social_url != "BLANK":
                    if social.lower() in social_url.lower():
                        validated_data[social] = social_url
                        logger.info(f"✅ Valid {social} found for {company}: {social_url}")
            
            # Owner and Address (no validation needed)
            for field in ["Owner", "Address"]:
                value = data_dict.get(field, "").strip()
                if value and value != "BLANK":
                    validated_data[field] = value
            
            # Quality metrics
            validated_data["Data_Quality"] = data_dict.get("Data_Quality", "POOR")
            validated_data["Sources_Used"] = data_dict.get("Sources_Used", "Unknown")
            validated_data["Confidence_Score"] = data_dict.get("Confidence_Score", "0")
            validated_data["Validation_Notes"] = data_dict.get("Validation_Notes", "")
            
            return validated_data
            
        return None
        
    except Exception as e:
        logger.error(f"Error processing refined data for {company}: {e}")
        return None

# Load your list of firms
df = pd.read_csv("firms.csv")

# Define all expected columns
expected_columns = [
    "No.", 
    "Business Type", 
    "Company Name", 
    "Location", 
    "Website",
    "Founder(s)/Owner(s)/Director(s)",
    "Email",
    "Phone",
    "Facebook",
    "Instagram",
    "LinkedIn"
]

# Add any missing columns
for col in expected_columns:
    if col not in df.columns:
        df[col] = ""

# Regex patterns
email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
# More comprehensive phone pattern to match various formats
phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?(?:\d{3})\)?[-.\s]?\d{3}[-.\s]?\d{4}|\d{10}|(?:\+\d{1,3}[-.\s]?)?\d{5}[-.\s]?\d{5}'

for index, row in tqdm(df.iterrows(), total=df.shape[0]):
    try:
        # Check if website is missing or empty
        if not row['Website'] or pd.isna(row['Website']) or row['Website'].strip() == '':
            print(f"🔍 COMPREHENSIVE SEARCH for: {row['Company Name']} ({row['Business Type']}) in {row['Location']}")
            print("=" * 80)
            
            # Step 1: Collect data from all sources
            print(f"📊 Step 1: Collecting data from multiple sources...")
            
            # Source 1: Gemini AI
            print(f"🤖 Source 1: Gemini AI search...")
            gemini_result = get_company_details_from_gemini(row['Company Name'], row['Business Type'], row['Location'])
            
            # Source 2: Tavily Search
            print(f"🌐 Source 2: Tavily web search...")
            tavily_result = search_with_tavily(row['Company Name'], row['Business Type'], row['Location'])
            
            # Source 3: SERP API (Google Search)
            print(f"🔍 Source 3: SERP API Google search...")
            serp_result = search_with_serp_api(row['Company Name'], row['Business Type'], row['Location'])
            
            # Step 2: Have Gemini analyze and refine all collected data
            print(f"🧠 Step 2: Gemini analyzing and refining all data sources...")
            refined_result = refine_data_with_gemini(
                row['Company Name'], 
                row['Business Type'], 
                row['Location'],
                gemini_result,
                tavily_result,
                serp_result
            )
            
            # Step 3: Process and validate the refined result
            print(f"✅ Step 3: Processing and validating refined data...")
            validated_data = process_refined_data(
                row['Company Name'], 
                row['Business Type'], 
                row['Location'], 
                refined_result
            )
            
            if validated_data:
                found_data = False
                
                # Update DataFrame with validated data
                if "Website" in validated_data:
                    df.at[index, "Website"] = validated_data["Website"]
                    found_data = True
                    print(f"  🌐 Website: {validated_data['Website']}")
                
                if "Email" in validated_data:
                    df.at[index, "Email"] = validated_data["Email"]
                    found_data = True
                    print(f"  📧 Email: {validated_data['Email']}")
                
                if "Phone" in validated_data:
                    df.at[index, "Phone"] = validated_data["Phone"]
                    found_data = True
                    print(f"  📞 Phone: {validated_data['Phone']}")
                
                if "Facebook" in validated_data:
                    df.at[index, "Facebook"] = validated_data["Facebook"]
                    found_data = True
                    print(f"  📘 Facebook: {validated_data['Facebook']}")
                
                if "Instagram" in validated_data:
                    df.at[index, "Instagram"] = validated_data["Instagram"]
                    found_data = True
                    print(f"  📷 Instagram: {validated_data['Instagram']}")
                
                if "LinkedIn" in validated_data:
                    df.at[index, "LinkedIn"] = validated_data["LinkedIn"]
                    found_data = True
                    print(f"  💼 LinkedIn: {validated_data['LinkedIn']}")
                
                if "Owner" in validated_data:
                    df.at[index, "Founder(s)/Owner(s)/Director(s)"] = validated_data["Owner"]
                    found_data = True
                    print(f"  👤 Owner: {validated_data['Owner']}")
                
                if "Address" in validated_data:
                    found_data = True
                    print(f"  📍 Address: {validated_data['Address']}")
                
                # Final result summary
                if found_data:
                    print(f"✅ SUCCESS: Found validated data for {row['Company Name']}")
                    print(f"   📊 Data Quality: {validated_data.get('Data_Quality', 'Unknown')}")
                    print(f"   📋 Sources Used: {validated_data.get('Sources_Used', 'Unknown')}")
                    print(f"   🎯 Confidence Score: {validated_data.get('Confidence_Score', '0')}/10")
                    if validated_data.get('Validation_Notes'):
                        print(f"   📝 Notes: {validated_data['Validation_Notes']}")
                    
                    # Log success
                    logger.info(f"SUCCESS: {row['Company Name']} - Quality: {validated_data.get('Data_Quality', 'Unknown')}")
                else:
                    print(f"❌ FINAL RESULT: No valid data found for {row['Company Name']}")
                    logger.warning(f"NO VALID DATA: {row['Company Name']} - All sources failed validation")
            else:
                print(f"❌ FINAL RESULT: All search methods failed for {row['Company Name']}")
                logger.error(f"COMPLETE FAILURE: {row['Company Name']} - All sources and validation failed")
            
            print("=" * 80)
        
        # Continue with regular scraping if website is available
        if row['Website'] and not pd.isna(row['Website']) and row['Website'].strip() != '':
            url = row["Website"].strip()
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            # Social links from homepage
            socials = extract_social_links(soup)
            df.at[index, "Facebook"] = socials["Facebook"]
            df.at[index, "Instagram"] = socials["Instagram"]
            df.at[index, "LinkedIn"] = socials["LinkedIn"]
            # Multi-page scraping
            urls_to_scrape = [url] + list(get_internal_links(soup, url))
            full_text = soup.get_text()
            for link in urls_to_scrape[1:]:
                try:
                    internal_html = requests.get(link, headers=headers, timeout=10).text
                    internal_soup = BeautifulSoup(internal_html, "html.parser")
                    full_text += "\n" + internal_soup.get_text()
                except:
                    pass
            # Clean up text
            full_text = full_text.replace('\xa0', ' ').replace('\u200b', ' ')
            full_text = ' '.join(full_text.split())
            # Extract and clean contacts
            emails = re.findall(email_pattern, full_text)
            phones = re.findall(phone_pattern, full_text)
            cleaned_emails, cleaned_phones = clean_contacts(emails, phones)
            df.at[index, "Email"] = ", ".join(cleaned_emails)
            df.at[index, "Phone"] = ", ".join(cleaned_phones)
    except Exception as e:
        print(f"Failed to process {row.get('Company Name', 'Unknown')}: {e}")
# Save to Excel with error handling
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

try:
    df.to_excel("interior_firm_contacts.xlsx", index=False)
    print("✅ Scraping complete. Data saved to 'interior_firm_contacts.xlsx'")
except PermissionError:
    # If the file is open, save with timestamp
    backup_filename = f"interior_firm_contacts_{timestamp}.xlsx"
    df.to_excel(backup_filename, index=False)
    print(f"⚠️  Original file was locked. Data saved to '{backup_filename}'")
except Exception as e:
    # If Excel fails, save as CSV as backup
    csv_filename = f"interior_firm_contacts_{timestamp}.csv"
    df.to_csv(csv_filename, index=False)
    print(f"⚠️  Excel save failed. Data saved as CSV: '{csv_filename}'")
    print(f"Error: {e}") 
# 🕷️ Advanced Web Scraper for Business Contact Information

A sophisticated Python web scraper that extracts comprehensive contact information from company websites using multiple AI-powered search strategies. This tool combines traditional web scraping with advanced AI APIs to find business details even when websites are missing or incomplete.

## 🌟 Features

### Core Capabilities
- **Multi-Source Data Collection**: Scrapes from company websites, business directories, and search engines
- **AI-Powered Search**: Uses Gemini AI, Tavily Search, and SERP API for comprehensive data gathering
- **Smart Validation**: Validates emails, phone numbers, and URLs before saving
- **Social Media Detection**: Automatically finds Facebook, Instagram, and LinkedIn profiles
- **Comprehensive Logging**: Detailed logging system for monitoring and debugging

### Advanced Features
- **Triple-Layer Search System**: 
  - Layer 1: Gemini AI with 40+ search strategies
  - Layer 2: Tavily web crawling with 45+ targeted queries
  - Layer 3: SERP API for direct Google search results
- **Data Quality Scoring**: Assigns quality scores (EXCELLENT/GOOD/FAIR/POOR) to collected data
- **Cross-Source Validation**: Compares data from multiple sources for accuracy
- **Industry-Specific Targeting**: Prevents cross-industry contamination
- **Accessibility Testing**: Validates that found URLs actually work

## 🛠️ Installation

### Prerequisites
- Python 3.7 or higher
- Internet connection
- API keys for Gemini, Tavily, and SERP API

### Step 1: Clone the Repository
```bash
git clone https://github.com/ajofficial223/Data_Scraper.git
cd Data_Scraper
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set Up API Keys
Edit the `scraper.py` file and replace the placeholder API keys:

```python
# Setup Gemini API
genai.configure(api_key="YOUR_GEMINI_API_KEY")

# Setup Tavily API
tavily_client = TavilyClient(api_key="YOUR_TAVILY_API_KEY")

# Setup SERP API
SERP_API_KEY = "YOUR_SERP_API_KEY"
```

#### Getting API Keys:
1. **Gemini AI**: Get your free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Tavily Search**: Sign up at [Tavily.com](https://tavily.com/) for web search API
3. **SERP API**: Get your key from [SerpApi.com](https://serpapi.com/) for Google search results

## 📊 Input Data Format

Create a CSV file named `firms.csv` with the following columns:
- `No.`: Serial number
- `Business Type`: Industry/business category
- `Company Name`: Exact company name
- `Location`: City/area where company is located
- `Website`: Company website (can be empty - the scraper will find it)

Example:
```csv
No.,Business Type,Company Name,Location,Website
1,Interior Design,ABC Interiors,Mumbai,
2,Interior Design,XYZ Designs,Delhi,https://xyzdesigns.com
```

## 🚀 Usage

### Basic Usage
```bash
python scraper.py
```

### What the Scraper Does:

1. **Reads Input**: Loads company data from `firms.csv`
2. **Website Scraping**: For companies with websites, scrapes contact information
3. **AI-Powered Search**: For companies without websites, uses AI to find them
4. **Data Validation**: Validates all collected information
5. **Excel Export**: Saves results to `interior_firm_contacts.xlsx`

### Output Columns:
- `Website`: Company website URL
- `Email`: Business email addresses
- `Phone`: Contact phone numbers
- `Facebook`: Facebook page URL
- `Instagram`: Instagram profile URL
- `LinkedIn`: LinkedIn company page URL
- `Founder(s)/Owner(s)/Director(s)`: Key personnel names
- Plus data quality metrics and source attribution

## 🔍 How It Works

### Traditional Web Scraping
For companies with existing websites:
1. Scrapes homepage and internal pages (contact, about, team)
2. Extracts emails using regex patterns
3. Finds phone numbers in various formats
4. Detects social media links
5. Validates and formats all data

### AI-Powered Discovery
For companies without websites:

#### Gemini AI Search (40+ Strategies)
- Basic company name searches
- Business directory searches (JustDial, IndiaMART, etc.)
- Social media platform searches
- Contact-specific queries
- Website domain variations

#### Tavily Web Crawling (45+ Queries)
- Comprehensive web crawling
- Domain-specific searches
- Owner/proprietor searches
- Location-based queries
- Industry-specific searches

#### SERP API Integration
- Direct Google search results
- Knowledge graph extraction
- Organic results processing
- Structured data extraction

### Data Refinement Process
1. **Collection**: Gather data from all three sources
2. **Analysis**: Gemini AI analyzes and cross-validates all data
3. **Quality Scoring**: Assigns confidence scores and quality ratings
4. **Validation**: Tests URLs, validates email formats, checks phone numbers
5. **Storage**: Saves only verified, high-quality data

## 📈 Performance Features

- **Parallel Processing**: Executes multiple searches simultaneously
- **Smart Retry Logic**: Handles API failures gracefully
- **Progress Tracking**: Shows real-time progress with tqdm
- **Comprehensive Logging**: Detailed logs in `scraper.log`
- **Error Recovery**: Continues processing even if individual companies fail

## 📝 Logging and Monitoring

The scraper creates detailed logs:
- `scraper.log`: General operation logs
- `gemini_failures.log`: Detailed failure analysis
- Console output: Real-time progress and results

## 🔧 Configuration Options

### Timeout Settings
- Website access timeout: 5 seconds
- API request timeout: Configurable per API

### Validation Rules
- Email format validation with regex
- Indian phone number format validation
- URL accessibility testing
- Social media URL verification

### Quality Thresholds
- Data quality scoring (EXCELLENT/GOOD/FAIR/POOR)
- Confidence scoring (1-10 scale)
- Source attribution tracking

## 📊 Sample Results

The scraper generates comprehensive reports including:
- **Success Rate**: Percentage of companies with found data
- **Data Quality Metrics**: Quality distribution across results
- **Source Attribution**: Which APIs found which data
- **Validation Results**: How many URLs/emails/phones were validated

## 🛡️ Error Handling

- **API Rate Limiting**: Handles rate limits gracefully
- **Network Errors**: Retries failed requests
- **Data Validation**: Rejects invalid or suspicious data
- **File Locking**: Handles Excel file access issues
- **Encoding Issues**: Proper UTF-8 handling for international characters

## 🔒 Privacy and Ethics

- **Respectful Scraping**: Implements delays and respects robots.txt
- **Data Accuracy**: Cross-validates information from multiple sources
- **No Personal Data**: Focuses only on business contact information
- **Transparent Logging**: All actions are logged for accountability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:
1. Check the `scraper.log` file for error details
2. Verify your API keys are valid and have sufficient quota
3. Ensure your input CSV file follows the correct format
4. Create an issue on GitHub with detailed error information

## 🔄 Updates and Maintenance

This scraper is actively maintained and updated to:
- Handle changes in website structures
- Improve AI search strategies
- Add new data sources
- Enhance validation rules
- Fix bugs and improve performance

---

**Note**: This tool is designed for legitimate business research purposes. Please ensure you comply with all applicable laws and website terms of service when using this scraper. 
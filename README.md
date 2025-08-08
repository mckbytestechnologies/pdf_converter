# Flask PDF Converter

A Flask-based web application that converts uploaded Excel files into professional, multi-page PDF statements.  
Ideal for billing statements, reports, and invoices with custom headers, tables, and branding.  
Ensures clean table formatting, consistent alignment, and proper pagination for production use.

## Features
- Upload Excel/XLSX files via a browser
- Parse and validate data with Pandas
- Generate professional PDF statements using FPDF
- Multi-page support with automatic pagination
- Customizable headers, footers, and branding
- Optional QR codes and payment instructions

## Create & Run

Follow these steps to set up and run the application:

```bash
# 1. Clone the repository
git clone https://github.com/mckbytestechnologies/pdf_converter.git
cd pdf_converter

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the Flask app
python app.py

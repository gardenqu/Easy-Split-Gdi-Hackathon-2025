import pytesseract
from PIL import Image
import re

def extract_receipt_data(image_path):
    """
    Complete receipt processing: OCR + parsing
    Returns structured JSON data from receipt image
    """
    # Step 1: Extract text from image
    def quick_receipt_read(image_path):
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text

    # Step 2: Parse text into structured data
    def parse_receipt_text(text):
        lines = text.split('\n')
        parsed_data = {
            'store_name': '',
            'items': [],
            'subtotal': '',
            'total': '',
            'tax': '',
            'date': '',
            'cashier': ''
        }
        
        # Clean the text first
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 1:  # Remove empty/short lines
                cleaned_lines.append(line)
        
        # Extract store name (look for store names in first few lines)
        store_keywords = ['STORE', 'MARKET', 'SHOP', 'GROCERY', 'SUPER', 'MART', 'FOOD', 'SAVE']
        for i, line in enumerate(cleaned_lines[:5]):
            # Look for lines that are likely store names (not prices, not too short)
            if (len(line) > 2 and len(line) < 50 and 
                not re.search(r'\d+\.\d{2}', line) and  # No prices
                any(keyword in line.upper() for keyword in store_keywords) or
                (re.search(r'[A-Z][a-z]+', line) and not re.search(r'\d', line))):  # Proper capitalization, no numbers
                parsed_data['store_name'] = line
                break
        
        # Extract total (look for TOTAL line)
        for i, line in enumerate(cleaned_lines):
            if 'TOTAL' in line.upper():
                # Find amounts in the TOTAL line
                amounts = re.findall(r'[0-9]+\.[0-9]{2}|[0-9]+', line)
                if amounts:
                    parsed_data['total'] = amounts[-1]
        
        # Extract subtotal
        for i, line in enumerate(cleaned_lines):
            if 'SUBTOTAL' in line.upper():
                amounts = re.findall(r'[0-9]+\.[0-9]{2}|[0-9]+', line)
                if amounts:
                    parsed_data['subtotal'] = amounts[-1]
        
        # Extract items - be more selective
        for i, line in enumerate(cleaned_lines):
            line_upper = line.upper()
            
            # Skip lines that are clearly not items
            skip_words = ['TOTAL', 'SUBTOTAL', 'TAX', 'CASH', 'CHANGE', 'ITEMS SOLD', 'DISCOUNT', 'RP', 'T#', 'OPEN', 'HOURS']
            if any(skip_word in line_upper for skip_word in skip_words):
                continue
            
            # Look for actual product names (not random text)
            if (re.search(r'[A-Za-z]{3,}', line) and  # At least 3 letters
                not re.search(r'[0-9]{5,}', line) and  # Not long number sequences
                len(line) > 3 and len(line) < 50):     # Reasonable length
                
                # Check if this line or next line has a price
                prices = re.findall(r'[0-9]+\.[0-9]{2}', line)
                if prices and float(prices[0]) < 100:  # Reasonable price
                    item_name = re.sub(r'[0-9]+\.[0-9]{2}', '', line).strip()
                    if len(item_name) > 2:  # Valid item name
                        parsed_data['items'].append({
                            'name': item_name,
                            'price': prices[0]
                        })
                else:
                    # Check next line for price
                    if i + 1 < len(cleaned_lines):
                        next_prices = re.findall(r'[0-9]+\.[0-9]{2}', cleaned_lines[i + 1])
                        if next_prices and float(next_prices[0]) < 100:
                            parsed_data['items'].append({
                                'name': line,
                                'price': next_prices[0]
                            })
        
        # Extract tax
        for i, line in enumerate(cleaned_lines):
            if 'TAX' in line.upper():
                amounts = re.findall(r'[0-9]+\.[0-9]{2}|[0-9]+', line)
                if amounts:
                    parsed_data['tax'] = amounts[-1]
        
        return parsed_data

    # Execute the pipeline
    text = quick_receipt_read(image_path)
    result = parse_receipt_text(text)
    return result
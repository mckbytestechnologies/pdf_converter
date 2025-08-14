from flask import Flask, render_template, request, send_file, redirect, url_for
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
from fpdf import FPDF

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

class StatementGenerator:
    def __init__(self, excel_file_path):
        self.df = pd.read_excel(excel_file_path)
        self.practice_info = {
            'name': "Family Internal Medicine PA Inc",
            'doctor': "Vinod Kumar Nagabhairu, MD",
            'address': "PO Box 1549",
            'city_state_zip': "Mechanicsburg PA 17055-9049",
            'billing_phone': "717-527-5701",
            'billing_fax': "914-202-0292"
        }
    
    def generate_pdf(self, output_path):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=False)
        grouped = self.df.groupby(['Patient ID', 'Patient Name'])

        for (patient_id, patient_name), group in grouped:
            pdf.add_page()
            self._add_first_page_content(pdf, patient_id, patient_name, group)

            if len(group) > 8:
                remaining_data = group.iloc[8:]
                page_num = 2
                total_pages = 1 + (len(remaining_data) // 25 + (1 if len(remaining_data) % 25 else 0))

                for i in range(0, len(remaining_data), 25):
                    pdf.add_page()
                    self._add_continuation_page(
                        pdf, patient_id, patient_name,
                        remaining_data.iloc[i:i+25],
                        page_num, total_pages
                    )
                    page_num += 1

        pdf.output(output_path)


    def _add_first_page_content(self, pdf, patient_id, patient_name, patient_data):
        header_y = 10
        card_y = 10
        address_y = 55
        payment_y = 55
        table_start_y = 100
        message_start_y = 190
        footer_start_y = 250
        
        # --- HEADER SECTION ---
        self._add_header(pdf, header_y, pdf.w * 0.55)
        
        account_no = patient_data.iloc[0].get('Account Number', '')
        total_balance = patient_data.iloc[0].get('Total Balance', 0.0)
        top_margin = 10
        header_y_start = top_margin

        page_width = pdf.w - 2 * pdf.l_margin
        
        header_left_width = page_width * 0.55
        header_right_width = page_width * 0.45
        
        self._add_header_card(
            pdf, 
            x_pos=pdf.l_margin + header_left_width, 
            y_pos=header_y_start,
            card_width=header_right_width,
            patient_id=patient_id, 
            patient_name=patient_name, 
            patient_data=patient_data.iloc[0]
        )
        
        # --- ADDRESS SECTION ---
        self._add_patient_address(pdf, address_y, pdf.w * 0.55, patient_data.iloc[0])
        self._add_payment_instructions(pdf, pdf.l_margin + pdf.w * 0.55, payment_y, pdf.w * 0.45)

        total_pages = 1 + max(0, (len(patient_data) - 8) // 25)
        self._add_page_info(pdf, total_pages)
        
        self._add_pink_separator(pdf)
        
        # --- BILLING TABLE SECTION ---
        pdf.set_fill_color(232, 244, 252)
        pdf.rect(0, table_start_y, pdf.w, pdf.h, 'F')
        
        pdf.set_y(table_start_y + 5)
        rows_to_show = patient_data.head(8)
        self._add_billing_table(pdf, rows_to_show)
        
        # --- MESSAGE AND SUMMARY SECTION ---
        pdf.set_y(message_start_y)
        self._add_important_message_and_summary(pdf, patient_id, patient_name, patient_data.iloc[0])

        pdf.set_y(footer_start_y)
        self._add_payment_instructions_footer(
        pdf,
        x_pos=pdf.w - 80,
        y_pos=pdf.h - 40,  
        width=60
    )

        self._add_footer(pdf)

    def _add_continuation_page(self, pdf, patient_id, patient_name, patient_data, page_num, total_pages):
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, f"Patient: {patient_name} ({patient_id}) - Page {page_num} of {total_pages}", ln=1)
        
        self._add_pink_separator(pdf)
        
        pdf.set_fill_color(232, 244, 252)
        pdf.rect(0, 25, pdf.w, pdf.h, 'F')
        
        pdf.set_y(30)
        self._add_billing_table(pdf, patient_data)
        
        pdf.set_y(pdf.h - 30)
        self._add_footer(pdf)

    def _add_header(self, pdf, y_pos, width):
        start_y = y_pos

        line_height = 2
        pdf.set_draw_color(0, 125, 225)
        pdf.set_fill_color(0, 125, 225)
        border_width = width * 0.9

        pdf.rect(pdf.l_margin, start_y, border_width, line_height, 'F')

        y_pos += line_height + 2
        pdf.set_xy(pdf.l_margin, y_pos)

        pdf.set_font('Arial', 'B', 12) 
        pdf.multi_cell(width, 5, self.practice_info['name'], ln=1, align='C')
        pdf.multi_cell(width, 6, self.practice_info['doctor'], ln=1, align='C')
        pdf.set_x(pdf.l_margin)

        pdf.set_font('Arial', '', 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(width, 4, self.practice_info['address'], ln=1, align='C') 
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(width, 4, self.practice_info['city_state_zip'], ln=1, align='C') 

        pdf.ln(3) 
        pdf.set_x(pdf.l_margin)

        phone_label_width = width * 0.4
        phone_value_width = width * 0.6
        pdf.set_font('Arial', '', 9) 
        pdf.cell(phone_label_width, 4, "Billing Phone:", ln=0, align='C')  
        pdf.cell(phone_value_width, 4, self.practice_info['billing_phone'], ln=1, align='C') 
        pdf.set_x(pdf.l_margin)
        pdf.cell(phone_label_width, 4, "Billing Fax:", ln=0, align='C')  
        pdf.cell(phone_value_width, 4, self.practice_info['billing_fax'], ln=1, align='C') 

        return pdf.get_y() - start_y

    def _add_header_card(self, pdf, x_pos, y_pos, card_width, patient_id, patient_name, patient_data):
        start_y = y_pos
        
        line_height = 4  
        small_font = 6   
        bold_font = 7    
        border_color = (0, 0, 200)
        
        pdf.set_xy(x_pos, y_pos)
        pdf.set_draw_color(*border_color)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', bold_font)
        pdf.cell(card_width, line_height, "IF PAYING BY CREDIT CARD PLEASE FILL OUT BELOW", ln=1, border=1, align='C')
        
        pdf.set_x(x_pos)
        pdf.set_font('Arial', 'B', small_font)
        pdf.cell(card_width, line_height, "CHECK CARD USING FOR PAYMENT", ln=1, border=1, align='C')
        
        logo_y = pdf.get_y()
        logos = ['images/mastercard.png', 'images/discover.png', 'images/amex.png', 'images/visa.png']
        logo_width = 12  
        logo_height = 6   
        checkbox_size = 2 
        

        total_width = (logo_width + checkbox_size + 2) * len(logos)
        start_x = x_pos + (card_width - total_width) / 2

        pdf.rect(x_pos, logo_y, card_width, logo_height + 3, 'D') 
        
        current_x = start_x
        for logo in logos:
   
            pdf.set_xy(current_x, logo_y + (logo_height - checkbox_size)/2 + 1.5)
            pdf.cell(checkbox_size, checkbox_size, "", border=1, ln=0)
            

            pdf.image(logo, x=current_x + checkbox_size + 1, y=logo_y + 1.5, w=logo_width, h=logo_height)
            current_x += logo_width + checkbox_size + 2
        
        pdf.set_y(logo_y + logo_height + 3) 

        col_width = card_width / 2
        pdf.set_font('Arial', 'B', small_font)
        pdf.set_text_color(0, 0, 0)

        details_height = line_height * 3
        pdf.rect(x_pos, pdf.get_y(), card_width, details_height, 'D')
        
        pdf.set_x(x_pos)
        pdf.cell(col_width, line_height, "CARD NUMBER", border='LR', ln=0)
        pdf.cell(col_width, line_height, "3 DIGIT SECURITY CODE", border='LR', ln=1)
        
        pdf.line(x_pos, pdf.get_y(), x_pos + card_width, pdf.get_y())

        pdf.set_x(x_pos)
        pdf.cell(col_width, line_height, "SIGNATURE", border='LR', ln=0)
        pdf.cell(col_width, line_height, "EXP. DATE", border='LR', ln=1)

        pdf.line(x_pos, pdf.get_y(), x_pos + card_width, pdf.get_y())

        pdf.set_x(x_pos)
        pdf.cell(col_width, line_height, "NAME ON CARD", border='LR', ln=0)
        pdf.cell(col_width, line_height, "ZIP CODE", border='LR', ln=1)
        
        pdf.set_x(x_pos)
        pdf.cell(col_width, line_height, "PATIENT NAME", border=1, ln=0)
        pdf.cell(col_width, line_height, "AMOUNT ENCLOSED/CHARGED", border=1, ln=1)
        
        pdf.set_x(x_pos)
        pdf.set_font('Arial', '', small_font)
        pdf.cell(col_width, line_height, patient_name, border='LRB', ln=0)
        pdf.cell(col_width, line_height, "", border='LRB', ln=1)
        
        date_width = card_width * 0.3
        amount_width = card_width * 0.3
        acct_width = card_width * 0.4
        
        statement_date = patient_data.get('Statement Date')
        date_str = statement_date.strftime('%m/%d/%Y') if pd.notna(statement_date) else ""
        amount_due = patient_data.get('Total Balance', 0.0)
        account_no = patient_data.get('Account Number', '')
        
        pdf.rect(x_pos, pdf.get_y(), card_width, line_height, 'D')
        
        pdf.set_x(x_pos)
        pdf.set_font('Arial', 'B', small_font)
        pdf.cell(date_width, line_height, "STATEMENT DATE", border='R', ln=0)
        
        pdf.line(x_pos + date_width, pdf.get_y(), x_pos + date_width, pdf.get_y() + line_height)
        
        pdf.set_font('Arial', 'B', small_font)
        pdf.set_text_color(255, 0, 0)
        pdf.cell(amount_width, line_height, "PAY THIS AMOUNT", border='R', ln=0)
        

        pdf.line(x_pos + date_width + amount_width, pdf.get_y(), 
                x_pos + date_width + amount_width, pdf.get_y() + line_height)

        pdf.set_font('Arial', 'B', small_font)
        pdf.set_text_color(0, 0, 0) 
        pdf.cell(acct_width, line_height, "ACCOUNT NUMBER", border=0, ln=1)

        pdf.rect(x_pos, pdf.get_y(), card_width, line_height, 'D')

        pdf.set_x(x_pos)
        pdf.set_font('Arial', '', small_font)
        pdf.cell(date_width, line_height, date_str, border='1', ln=0)
        
        pdf.set_font('Arial', 'B', small_font)
        pdf.set_text_color(255, 0, 0)
        pdf.cell(amount_width, line_height, f"${amount_due:.2f}", border='1', ln=0)
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font('Arial', '', small_font)
        pdf.cell(acct_width, line_height, str(account_no), border='1', ln=1)
        return pdf.get_y() - start_y

    def _add_page_info(self, pdf, total_pages):
        pdf.set_font('Arial', '', 8)
        y_pos = pdf.get_y()
        checkbox_size = 3
        checkbox_x = 20
        checkbox_y = y_pos + 0.5
        pdf.rect(checkbox_x, checkbox_y, checkbox_size, checkbox_size)
        text_x = checkbox_x + checkbox_size + 2
        pdf.set_xy(text_x, y_pos)
        pdf.cell(0, 4, "To ensure proper credit, please detach and return top portion with your payment.", ln=0)
        pdf.set_xy(170, y_pos)
        pdf.cell(0, 4, f"Page 1 of {total_pages}", ln=1, align='R')
        pdf.ln(3)

    def _add_pink_separator(self, pdf):
        line_y = pdf.get_y() - 1
        line_start_x = 20
        line_end_x = pdf.w - 20
        pdf.set_draw_color(255, 105, 180)
        pdf.line(line_start_x, line_y, line_end_x, line_y)
        pdf.set_draw_color(0, 0, 0)

    def _add_patient_address(self, pdf, y_pos, width, patient_data):
        import os
        
        start_y = y_pos
        line_height = 4
        left_indent = 15

        zip_code = str(patient_data.get('ZipCode', '')).strip()

        pdf.set_xy(pdf.l_margin, start_y)
        pdf.set_fill_color(0, 125, 225)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 7)
        pdf.cell(width * 0.8, line_height, "CONFIDENTIALLY ADDRESSED TO:", ln=1, fill=True, align='C')

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 8)
        pdf.set_x(left_indent)
        pdf.cell(0, 4, f"10445 1 MB 0.672 ******************AUTO*MIXED AADC {zip_code}", ln=1)

        pdf.set_x(left_indent)
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, line_height, patient_data.get('Patient Name', ''), ln=1)

        address_line1 = patient_data.get('Patient Address1', '')
        address_line2 = f"{patient_data.get('City', '')}, {patient_data.get('State', '')} {zip_code}"

        pdf.set_x(left_indent)
        pdf.cell(0, line_height, address_line1, ln=1)
        pdf.set_x(left_indent)
        pdf.cell(0, line_height, address_line2, ln=1)

     
        barcode_filename = f"temp_barcode_{zip_code}.png"
        self._generte_posatnet_barcode_image(zip_code, barcode_filename)

        # Add barcode image
        barcode_y = pdf.get_y() + 2
        pdf.image(barcode_filename, x=left_indent, y=barcode_y, w=50, h=10)

        if os.path.exists(barcode_filename):
            os.remove(barcode_filename)


    def _generate_postnet_barcode_image(self, zip_code, filename):
        """Helper method to generate POSTNET barcode image dynamically"""
        import matplotlib.pyplot as plt
        import numpy as np

        clean_zip = zip_code.replace('-', '')

        # Calculate checksum
        def calculate_checksum(zip_str):
            total = sum(int(d) for d in zip_str if d.isdigit())
            return (10 - (total % 10)) % 10

        checksum = str(calculate_checksum(clean_zip))
        full_code = clean_zip + checksum

        # POSTNET digit patterns
        patterns = {
            '0': '11000', '1': '00011', '2': '00101', '3': '00110',
            '4': '01001', '5': '01010', '6': '01100', '7': '10001',
            '8': '10010', '9': '10100'
        }

        barcode_pattern = ['1'] 
        for digit in full_code:
            barcode_pattern.extend(list(patterns[digit]))
        barcode_pattern.append('1') 
        bar_height = [0.125 if bit == '1' else 0.05 for bit in barcode_pattern]
        bar_positions = np.arange(len(barcode_pattern))

        fig, ax = plt.subplots(figsize=(6, 1))
        ax.bar(bar_positions, bar_height, width=0.8, color='black')
        ax.axis('off')
        ax.set_ylim(0, 0.15)
        ax.set_xlim(-1, len(barcode_pattern))
        plt.subplots_adjust(left=0.05, right=0.95)

        plt.savefig(filename, bbox_inches='tight', pad_inches=0.1, dpi=300)
        plt.close()


    def _add_payment_instructions(self, pdf, x_pos, y_pos, width):
        start_y = y_pos
        line_height = 4 
        left_padding = x_pos + 3 
        content_width = width - (left_padding - x_pos)

        pdf.set_xy(x_pos, start_y)
        pdf.set_fill_color(0, 125, 225)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 7) 
        pdf.cell(width * 0.8, line_height, "MAKE CHECKS PAYABLE AND MAIL TO:", ln=1, fill=True, align='C')

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 9) 
        pdf.set_xy(left_padding, pdf.get_y())
        pdf.multi_cell(content_width, line_height - 1, self.practice_info['name'], align='L')

        pdf.set_font('Arial', '', 9) 
        pdf.set_x(left_padding)
        pdf.multi_cell(content_width, line_height - 1, self.practice_info['address'], align='L')

        pdf.set_x(left_padding)
        pdf.multi_cell(content_width, line_height - 1, self.practice_info['city_state_zip'], align='L')

        image_path = 'images/paypal.png'
        image_width = 8
        image_height = 8
        line_height = 3.5

        text_x = x_pos + image_width + 1
        text_width = width - image_width - 1

        paypal_lines = [
            "Pay FAMILY INTERNAL MEDICINE.",
            "Go to paypal.me/FimPAInc and type in the amount.",
            "Since it's PayPal, it's easy...",
            "Paypal.me/FimPAInc"
        ]

        start_y = pdf.get_y() + 5

        pdf.image(image_path, x=x_pos, y=start_y, w=image_width, h=image_height)

        pdf.set_font('Arial', '', 8)
        pdf.set_xy(text_x, start_y)

        for i, line in enumerate(paypal_lines):
            pdf.set_x(text_x)
            if i == len(paypal_lines) - 1:

                pdf.set_text_color(0, 0, 255) 
                pdf.cell(text_width, line_height, line, ln=1, link="https://paypal.me/FimPAInc")
                pdf.set_text_color(0, 0, 0)  
            else:
                pdf.cell(text_width, line_height, line, ln=1)

        return pdf.get_y() - y_pos
    
    

    def _add_billing_table(self, pdf, patient_data, is_continuation=False):
        headers = [
            "Date of Service", "Visit ID", "Description", "CPT", "Charge",
            "Payments Insurance", "Adjustment Patient", "Balance"
        ]
    
        col_widths = [25, 20, 50, 15, 20, 25, 25, 15]
        row_height = 7

        table_start_x = pdf.l_margin
        table_start_y = pdf.get_y()

        pdf.set_fill_color(211, 211, 211)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_xy(table_start_x, table_start_y)

        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], row_height, header, border=0, align='C', fill=True)
        pdf.ln(row_height)

        if is_continuation:
            pdf.set_draw_color(0, 0, 0)
            pdf.rect(table_start_x, table_start_y, sum(col_widths), row_height)
            table_start_y += row_height 

   
        pdf.set_font('Arial', '', 8)
        pdf.set_fill_color(232, 244, 252)

        content_height = 0
        row_heights = []
        
        for _, row in patient_data.iterrows():
            description = str(row['Procedure'])
            if pd.notna(row.get('Reference')):
                description += f"\nREF: {row['Reference']}"

            desc_lines = max(1, int(pdf.get_string_width(description) / (col_widths[2] - 2)) + 1)
            cell_height = 4 * desc_lines
            row_heights.append(cell_height)
            content_height += cell_height

        for idx, (_, row) in enumerate(patient_data.iterrows()):
            date_str = row['Date Of Service'].strftime('%m/%d/%Y') if pd.notna(row['Date Of Service']) else ""
            if pdf.get_string_width(date_str) > col_widths[0] - 2:
                date_str = date_str[:8]  
            
            description = str(row['Procedure'])
            if pd.notna(row.get('Reference')):
                description += f"\nREF: {row['Reference']}"
            
            cell_height = row_heights[idx]
            y_start = pdf.get_y()
            
            pdf.rect(table_start_x, y_start, sum(col_widths), cell_height, 'F')

            x_pos = table_start_x
            pdf.set_xy(x_pos, y_start)
            pdf.cell(col_widths[0], cell_height, date_str, align='L')
            
            x_pos += col_widths[0]
            pdf.set_xy(x_pos, y_start)
            pdf.cell(col_widths[1], cell_height, str(row['Visit ID']), align='L')
            
            x_pos += col_widths[1]
            pdf.set_xy(x_pos, y_start)
            pdf.multi_cell(col_widths[2], 4, description, align='L')
            
            x_pos = table_start_x + sum(col_widths[:3])
            pdf.set_xy(x_pos, y_start)
            pdf.cell(col_widths[3], cell_height, str(row.get('CPT', '')), align='L')
            
            x_pos += col_widths[3]
            pdf.set_xy(x_pos, y_start)
            pdf.cell(col_widths[4], cell_height, f"${row.get('Charge', 0.0):.2f}", align='R')
            
            x_pos += col_widths[4]
            pdf.set_xy(x_pos, y_start)
            pdf.cell(col_widths[5], cell_height, f"(${row.get('Insurance Payment', 0.0):.2f})", align='R')
            
            x_pos += col_widths[5]
            pdf.set_xy(x_pos, y_start)
            pdf.cell(col_widths[6], cell_height, f"(${row.get('Adjustment', 0.0):.2f})", align='R')
            
            x_pos += col_widths[6]
            pdf.set_xy(x_pos, y_start)
            pdf.cell(col_widths[7], cell_height, f"${row.get('Balance', 0.0):.2f}", align='R')

            pdf.set_y(y_start + cell_height)

        border_end_y = 190 
        current_y = pdf.get_y()

        total_height = min(border_end_y - table_start_y, current_y + 60)
        
        pdf.set_draw_color(0, 0, 0)
        pdf.rect(table_start_x, table_start_y, sum(col_widths), total_height)
        
        if current_y < border_end_y:
            pdf.set_y(border_end_y)
        else:
            pdf.set_y(current_y)

    def _add_important_message_and_summary(self, pdf, patient_id, patient_name, patient_data):
        message_x = 10
        message_y = 190
        message_width = pdf.w * 0.65 - 15
        summary_width = pdf.w * 0.35 - 10
        
        pdf.set_fill_color(211, 211, 211)
        pdf.set_draw_color(0,0,0)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_xy(message_x, message_y)
        pdf.cell(message_width, 6, "Important Message From Our Billing Department", ln=1, fill=True, border=1, align='C')
        pdf.set_font('Arial', '', 9)
        pdf.set_x(message_x + 1)
        message_text = (
            "Thank you for selecting Family Internal Medicine PA Inc for your healthcare needs during your stay at Encompass Health of York. "
            "This statement represents your most recent charges, as well as the balance now due. Patient balance is due in full upon presentation of this statement. "
            "As a courtesy, we have billed your insurance company. Any charges denied or not paid by your insurance company will be transferred to patient responsibility.\n\n"
            "If you have questions as to how your insurance paid or elected not to pay, please call the insurance company directly. "
            "For questions regarding your account not related to insurance, please call our business office 717-527-5701, Monday through Friday between 8:30 am - 5:30 pm\n\n"
            "Thank you!"
        )
        pdf.multi_cell(message_width - 2, 4, message_text)
        
        message_end_y = pdf.get_y()
        pdf.rect(message_x, message_y, message_width, message_end_y - message_y)
        
        pdf.set_xy(message_width + 15, message_y)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(summary_width, 5, "ACCOUNT SUMMARY", ln=1)
        pdf.set_font('Arial', '', 9)
        pdf.ln(5)
        statement_date = patient_data.get('Statement Date')
        statement_date = statement_date.strftime('%m/%d/%Y') if pd.notna(statement_date) else ""
        amount_due = patient_data.get('Total Balance', 0.0)
        label_width = 30
        value_width = summary_width - label_width
        pdf.set_x(message_width + 15)
        pdf.cell(label_width, 4, "Patient ID:", ln=0)
        pdf.cell(value_width, 4, str(patient_id)[:15], ln=1)
        pdf.set_x(message_width + 15)
        pdf.cell(label_width, 4, "Patient Name:", ln=0)
        pdf.cell(value_width, 4, patient_name[:20], ln=1)
        pdf.set_x(message_width + 15)
        pdf.cell(label_width, 4, "Balance:", ln=0)
        pdf.cell(value_width, 4, f"${amount_due:.2f}", ln=1)
        pdf.set_x(message_width + 15)
        pdf.cell(label_width, 4, "Statement Date:", ln=0)
        pdf.cell(value_width, 4, statement_date, ln=1)
        
        box_x = message_width + 15
        box_y = pdf.get_y() + 2
        box_width = summary_width
        box_height = 12
        pdf.set_fill_color(211, 211, 211)
        pdf.set_draw_color(100, 100, 100)
        pdf.rect(box_x, box_y, box_width, box_height, 'FD')
        pdf.set_xy(box_x, box_y + 1)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(box_width, 5, "AMOUNT DUE NOW", ln=1, align='C')
        pdf.set_font('Arial', 'B', 10)
        pdf.set_xy(box_x, box_y + 7)
        pdf.cell(box_width, 6, f"${amount_due:.2f}", ln=1, align='C')
        pdf.ln(5)
        pdf.set_font('Arial', '', 10)
        pdf.set_x(message_width + 15)
        pdf.multi_cell(summary_width, 3, f"Billing Phone: {self.practice_info['billing_phone']}",align='C')
        pdf.ln(2)
        pdf.set_x(message_width + 15)
        pdf.multi_cell(summary_width, 3, f"Billing Fax: {self.practice_info['billing_fax']}",align='C')
        
    

    def _add_payment_instructions_footer(self, pdf, x_pos, y_pos, width):
        start_y = y_pos
        line_height = 4
        left_padding = x_pos + 3
        content_width = width - (left_padding - x_pos)

        image_path = 'images/paypal.png'
        image_width = 8
        image_height = 8
        line_height = 3.5

        text_x = x_pos + image_width + 1
        text_width = width - image_width - 1

        paypal_lines = [
            "Pay FAMILY INTERNAL MEDICINE.",
            "Go to paypal.me/FimPAInc and type in the amount.",
            "Since it's PayPal, it's easy...",
            "Paypal.me/FimPAInc"
        ]
        
        start_y = pdf.get_y() + 5

        pdf.image(image_path, x=x_pos, y=start_y, w=image_width, h=image_height)

        pdf.set_font('Arial', '', 8)
        pdf.set_xy(text_x, start_y)
        for line in paypal_lines:
            pdf.set_x(text_x)
            if line == "Paypal.me/FimPAInc":
                pdf.set_text_color(0, 0, 255) 
                pdf.set_font('', 'U') 
                pdf.cell(text_width, line_height, line, ln=1, link="https://paypal.me/FimPAInc")
                pdf.set_text_color(0, 0, 0)  
                pdf.set_font('Arial', '', 8)
            else:
                pdf.cell(text_width, line_height, line, ln=1)

        return pdf.get_y() - y_pos


    def _add_footer(self, pdf):
        FOOTER_HEIGHT = 30
        bottom_margin = 10
        footer_y = pdf.h - FOOTER_HEIGHT - bottom_margin

        pdf.set_y(footer_y)
        pdf.set_x(30)  
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(pdf.w - 80, 5, "Thank You from the Staff at", ln=1, align='C') 
        pdf.set_x(30)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(pdf.w - 80, 5, self.practice_info['name'], ln=1, align='C')
        pdf.set_x(30)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(pdf.w - 80, 5, self.practice_info['doctor'], ln=1, align='C')

        pdf.set_font('Arial', '', 9)
        pdf.set_x(30)
        pdf.cell(
            pdf.w - 80,
            5,
            f"{self.practice_info['address']}, {self.practice_info['city_state_zip']}",
            ln=1,
            align='C'
        )

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"statements_{timestamp}.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            try:
                generator = StatementGenerator(upload_path)
                generator.generate_pdf(output_path)
                return redirect(url_for('download_file', filename=output_filename))
            except Exception as e:
                return f"An error occurred: {e}"
    return render_template('upload.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(
        os.path.join(app.config['UPLOAD_FOLDER'], filename),
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True)
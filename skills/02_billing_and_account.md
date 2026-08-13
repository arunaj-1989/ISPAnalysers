# Skill 02: Billing, Invoice & Account Administration

## Issue Code Index
- `ACCOUNT_SUSPEND_REQUEST`
- `BILL_ENQUIRY`
- `DISCONNECTION_REQUEST`
- `INVOICE_REQUEST`
- `LOGIN_DETAILS_ENQUIRY`
- `PAYMENT_CONFIRMATION`

---

### 1. ACCOUNT_SUSPEND_REQUEST
- **Keywords:** "கொஞ்ச நாள் ஹோல்ட் பண்ணுங்க", "ஊருக்கு போறேன் நிறுத்துங்க", "temporary hold", "suspend service"
- **SOP:**
  1. Verify minimum suspension policy eligibility (e.g., minimum 15 days, maximum 90 days).
  2. Record start and end dates for suspension.
  3. Schedule auto-activation or pause bill generation during hold window.

### 2. BILL_ENQUIRY
- **Keywords:** "பில் எவ்வளோ வரணும்", "டூ டேட் எப்பப்போ", "due date", "bill amount details"
- **SOP:**
  1. Check account balance, pending dues, and current billing cycle expiry.
  2. Inform customer clearly of total payable amount and last payment date.

### 3. DISCONNECTION_REQUEST
- **Keywords:** "கனெக்ஷன் வேண்டாம் கேன்சல் பண்ணுங்க", "சர்வீஸ் க்ளோஸ் பண்ணுங்க", "permanent cancellation", "disconnect internet"
- **SOP:**
  1. Inquire reason for disconnection (Retention check).
  2. If persistent, check pending dues and guide on returning ISP equipment (ONT/Router).
  3. Initiate Deactivation Workflow.

### 4. INVOICE_REQUEST
- **Keywords:** "ஜிஎஸ்டி பில் வேணும்", "இன்வாய்ஸ் அனுப்புங்க", "tax invoice copy", "GST bill copy"
- **SOP:**
  1. Confirm customer email address and GST number (if business account).
  2. Email/WhatsApp official PDF invoice for requested billing cycle.

### 5. LOGIN_DETAILS_ENQUIRY
- **Keywords:** "ஆப் பாஸ்வேர்ட் மறந்துடுச்சு", "போர்ட்டல் லாக் இன் ஆகல", "app login error", "forgot user id"
- **SOP:**
  1. Verify registered mobile number (RMN).
  2. Trigger OTP reset or send login credential setup link via SMS.

### 6. PAYMENT_CONFIRMATION
- **Keywords:** "பணம் கட்டிட்டேன் இன்னும் ஆன் ஆகல", "பில் பே பண்ணியாச்சு", "recharge done not active", "payment screenshot"
- **SOP:**
  1. Analyze payment screenshot for Transaction ID/UTR, Amount, Date, and Payee Name (`Interjet`/`oksbi`).
  2. Search transaction in billing clearing house.
  3. On validation, reactivate connection manually in CRM.
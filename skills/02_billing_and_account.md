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
- **Keywords:** "temporary hold", "suspend service", "pause connection", "put account on hold"
- **SOP:**
  1. Verify minimum suspension policy eligibility (e.g., minimum 15 days, maximum 90 days).
  2. Record start and end dates for suspension.
  3. Schedule auto-activation or pause bill generation during hold window.

### 2. BILL_ENQUIRY
- **Keywords:** "due date", "bill amount details", "billing amount", "payment due"
- **SOP:**
  1. Check account balance, pending dues, and current billing cycle expiry.
  2. Inform customer clearly of total payable amount and last payment date.

### 3. DISCONNECTION_REQUEST
- **Keywords:** "permanent cancellation", "disconnect internet", "cancel connection", "close service"
- **SOP:**
  1. Inquire reason for disconnection (Retention check).
  2. If persistent, check pending dues and guide on returning ISP equipment (ONT/Router).
  3. Initiate Deactivation Workflow.

### 4. INVOICE_REQUEST
- **Keywords:** "tax invoice copy", "GST bill copy", "send invoice", "invoice request"
- **SOP:**
  1. Confirm customer email address and GST number (if business account).
  2. Email/WhatsApp official PDF invoice for requested billing cycle.

### 5. LOGIN_DETAILS_ENQUIRY
- **Keywords:** "app login error", "forgot user id", "forgot password", "portal login problem"
- **SOP:**
  1. Verify registered mobile number (RMN).
  2. Trigger OTP reset or send login credential setup link via SMS.

### 6. PAYMENT_CONFIRMATION
- **Keywords:** "recharge done not active", "payment screenshot", "payment completed but not active", "paid bill"
- **SOP:**
  1. Analyze payment screenshot for Transaction ID/UTR, Amount, Date, and Payee Name (`Interjet`/`oksbi`).
  2. Search transaction in billing clearing house.
  3. On validation, reactivate connection manually in CRM.
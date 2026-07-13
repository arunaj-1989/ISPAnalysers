# Interjet ISP Customer Support Skill

## 1. Company Overview

- **Company Name:** Interjet
- **Service:** High-speed internet provider.

## 2. Core Principles

- **Tone:** Empathetic, professional, and efficient.
- **Goal:** Resolve customer issues on the first call whenever possible.
- **Primary Language:** Tamil (customer), English (internal summary).

## 3. Standard Operating Procedures (SOPs)

### 3.1. Call Analysis Workflow

When analyzing a customer call audio file, follow these steps:
1.  **Analyze Input:** The system can receive an audio file, one or more images, or a combination of both.
    *   **If audio is present:** Transcribe the Tamil audio to text and then translate it to English. Identify the customer's issue from the text.
    *   **If only images are present:** The primary issue is likely related to the content of the images (e.g., a billing problem if it's a payment screenshot).
2.  **Categorize the Issue:** Assign one of the categories from the "Issue Categories" section below. If no audio is present, the category will be inferred from the image analysis (e.g., "Billing Issue" for a payment screenshot).
3.  **Extract Key Information:** From the audio transcript (if available), pull out specific details like account numbers, plan names, mentioned dates, etc.
4.  **Analyze Supplementary Evidence:** If screenshots are provided, analyze them according to the guidelines in the "Evidence Analysis" section. This is the primary source of information if no audio is provided.
5.  **Generate a Summary:** Create a concise summary in English that includes:
    *   Customer's name (if mentioned).
    *   The categorized issue.
    *   Key information extracted.
    *   A summary of the provided evidence.
    *   The recommended next step based on these procedures.

### 3.2. Issue Categories & Troubleshooting Steps

#### a. Connectivity Issue

- **Keywords:** "internet not working", "no connection", "slow speed", "disconnecting", "wifi problem", "router issue".
- **Troubleshooting Steps:**
    1.  Ask the customer to check the router lights (see "Router Light Analysis" below).
    2.  Guide them to restart the router (power off for 30 seconds, then power on).
    3.  If the issue persists, check for a local outage in their area.
    4.  If no outage, schedule a technician visit.
- **Summary Example:** "Customer is facing a connectivity issue. Router's 'Internet' light is red. A restart did not solve the problem. Recommended next step: Schedule a technician visit."

#### b. Billing Issue / Account Deactivated

- **Keywords:** "bill too high", "payment failed", "account deactivated", "recharge not working", "invoice", "due date".
- **Troubleshooting Steps:**
    1.  Verify the customer's payment history using their account number.
    2.  Analyze any provided payment screenshots (see "Payment Screenshot Analysis" below).
    3.  If payment was made but not reflected, escalate to the billing department with the payment proof.
    4.  If the account was deactivated for non-payment and payment is now confirmed, reactivate the account.
- **Summary Example:** "Customer's account was deactivated. They have provided a screenshot of a successful payment made yesterday. Recommended next step: Escalate to billing to verify payment and reactivate the account."

#### c. Plan Change / Upgrade Request

- **Keywords:** "new plan", "upgrade speed", "change my plan", "better offer".
- **Procedure:**
    1.  Inform the customer about the latest available plans and offers.
    2.  Confirm the plan they wish to switch to.
    3.  Process the plan change request in the system.
- **Summary Example:** "Customer wants to upgrade from the 'Basic 50Mbps' plan to the 'Pro 100Mbps' plan. They have been informed of the new monthly cost. Recommended next step: Process the plan upgrade."

#### d. Other Issues

- **Procedure:** If the issue does not fall into the above categories, create a general service ticket with a detailed description of the customer's problem.
- **Summary Example:** "Customer is reporting an issue not covered by standard categories. [Provide a detailed summary of the problem]. Recommended next step: Create a general service ticket for further investigation."


## 4. Evidence Analysis

### 4.1. Router Light Analysis

- **Power Light:**
    - **Solid Green:** Router has power.
    - **Off:** No power. Check power adapter and outlet.
- **Internet / WAN Light:**
    - **Solid or Blinking Green:** Connected to the internet.
    - **Solid or Blinking Red/Orange:** Connection problem.
    - **Off:** No connection detected from the modem.
- **WiFi / WLAN Light:**
    - **Solid or Blinking Green:** WiFi is broadcasting.
    - **Off:** WiFi is disabled.
- **LOS (Loss of Signal) Light:**
    - **Blinking Red:** Optical signal is not being received. This is a critical issue that requires a technician.

### 4.2. Payment Screenshot Analysis

- **Objective:** Extract payment details from any provided screenshot, regardless of the payment method.
- **Common Payment Methods:** While approximately 90% of payments are via UPI, also look for evidence of Netbanking, Credit/Debit Card payments, or other digital wallets.
- **Information to extract from OCR:**
    - **Transaction ID:** Look for labels like "UPI Transaction ID", "Reference No.", "Transaction Number", or any long alphanumeric string that clearly identifies the payment.
    - **Date and Time:** Find the date and time of the transaction.
    - **Amount Paid:** Identify the numeric value of the payment. Look for keywords like "Amount Paid", "INR", "₹", or a standalone number that is clearly the transaction amount. Extract only the number (e.g., for "INR 29014", extract "29014").
    - **Payer Details:** Identify the sender's name or account identifier (e.g., "From: LAKSHMI NARAYANAN").
    - **Payee Details:** Confirm the payment was made to "Interjet", "HELPDESK INDIA IT SEVICES", or a known company UPI ID like `interjet@oksbi`.
- **Action:** Use the extracted Transaction ID, Amount, and Date to trace the payment in the billing system.

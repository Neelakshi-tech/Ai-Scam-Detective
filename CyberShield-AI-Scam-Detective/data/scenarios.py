"""Detective Mode sample scenarios — India-context, fictional details.

Each DetectiveScenario contains:
  - A realistic but entirely fictional scam message
  - A list of selectable phrases shown to the user as checkboxes
  - The correct answers (indices into the phrases list)
  - An explanation revealed after submission

All organisation names, phone numbers, URLs, and amounts used here are
fictional and invented for educational purposes only. No affiliation with
or impersonation of any real institution is intended or claimed.
"""

from data.models import DetectiveScenario

SCENARIOS: list[DetectiveScenario] = [
    DetectiveScenario(
        scenario_id="parcel_delivery",
        title="📦 Fake Delivery / Refund Scam",
        message_text=(
            "Dear Customer, your Flipkart order #FL7823 could not be delivered. "
            "A customs clearance fee of ₹149 is required within 12 hours or your parcel "
            "will be returned. Pay now at: flipkart-delivery-fee.net "
            "For refund, share your UPI ID and OTP sent to your mobile. "
            "Failure to pay will result in a ₹500 penalty charge."
        ),
        phrases=[
            "Flipkart order #FL7823",                        # 0 — distractor (plausible reference)
            "customs clearance fee of ₹149",                 # 1 ✓ MONEY_REQUEST
            "within 12 hours",                               # 2 ✓ URGENCY
            "could not be delivered",                        # 3 — distractor (normal delivery language)
            "flipkart-delivery-fee.net",                     # 4 ✓ SUSPICIOUS_LINK
            "share your UPI ID and OTP",                     # 5 ✓ CREDENTIAL_REQUEST
            "Failure to pay will result in a ₹500 penalty", # 6 ✓ FEAR
            "Pay now",                                       # 7 ✓ URGENCY / MONEY_REQUEST
        ],
        correct_phrase_indices=[1, 2, 4, 5, 6, 7],
        explanation=(
            "**Customs clearance fee of ₹149 / Pay now** — Legitimate e-commerce platforms "
            "never ask for additional delivery fees via SMS or a third-party link. "
            "This is a money request tactic designed to steal a small amount from many victims.\n\n"
            "**Within 12 hours** — Artificial urgency is created to stop you from pausing "
            "and checking whether the message is genuine.\n\n"
            "**flipkart-delivery-fee.net** — This is NOT flipkart.com. The fake domain "
            "uses the brand name but adds words and a different extension to trick you. "
            "Always check the full domain carefully.\n\n"
            "**Share your UPI ID and OTP** — No legitimate company will ever ask for your OTP "
            "through a message. Your OTP is a one-time secret — sharing it gives someone "
            "full access to your payment account.\n\n"
            "**Failure to pay will result in a ₹500 penalty** — This is a fear tactic. "
            "The threat of an escalating penalty is designed to panic you into paying immediately."
        ),
        tactic_id="CREDENTIAL_REQUEST",
    ),
    DetectiveScenario(
        scenario_id="kyc_bank_scam",
        title="🏦 Fake KYC / Bank Account Scam",
        message_text=(
            "URGENT: IndiaFirst Bank — Your account KYC is incomplete. "
            "Your account will be permanently blocked within 24 hours. "
            "To avoid blocking, click here to update your KYC: indiafirst-kyc-update.in "
            "You will need to enter your full account number, ATM PIN, and Aadhaar number. "
            "This is a mandatory RBI directive. Do not ignore this notice."
        ),
        phrases=[
            "IndiaFirst Bank",                               # 0 ✓ IMPERSONATION / AUTHORITY
            "KYC is incomplete",                             # 1 — distractor (sounds like normal banking)
            "permanently blocked within 24 hours",           # 2 ✓ FEAR + URGENCY
            "indiafirst-kyc-update.in",                      # 3 ✓ SUSPICIOUS_LINK
            "account number, ATM PIN, and Aadhaar number",   # 4 ✓ CREDENTIAL_REQUEST
            "mandatory RBI directive",                       # 5 ✓ AUTHORITY (fake regulatory claim)
            "Do not ignore this notice",                     # 6 ✓ FEAR
            "To avoid blocking",                             # 7 — distractor (conditional phrasing)
        ],
        correct_phrase_indices=[0, 2, 3, 4, 5, 6],
        explanation=(
            "**IndiaFirst Bank** — Scammers use the name of a real or plausible bank to appear "
            "legitimate. The bank's name in an SMS does not verify the message is real. "
            "Always contact your bank through the number on the back of your card or their "
            "official website.\n\n"
            "**Permanently blocked within 24 hours** — Combining a severe threat with a tight "
            "deadline is a classic pressure tactic. Real banks do not send blocking notices via "
            "unsolicited SMS with a link.\n\n"
            "**indiafirst-kyc-update.in** — This is a fake domain. Your real bank's website "
            "will be something like indiafirstbank.in — not a variation with extra words.\n\n"
            "**Account number, ATM PIN, and Aadhaar number** — No bank or RBI directive will "
            "ever ask you to submit your ATM PIN or Aadhaar number through a link in an SMS. "
            "Anyone asking for these details is attempting to steal your identity and funds.\n\n"
            "**Mandatory RBI directive** — Invoking a real regulatory authority (RBI) adds "
            "false credibility. RBI does not send personal KYC notices by SMS."
        ),
        tactic_id="CREDENTIAL_REQUEST",
    ),
    DetectiveScenario(
        scenario_id="fake_job_offer",
        title="💼 Fake Work-from-Home Job Scam",
        message_text=(
            "Hi! We found your profile on Naukri.com and would like to offer you a "
            "work-from-home data entry role earning ₹50,000 per month. "
            "No experience needed — full training provided. "
            "To confirm your seat, pay a one-time registration fee of ₹999 via PhonePe "
            "and share your bank account details for salary setup. "
            "Only 3 seats remaining — offer closes tonight!"
        ),
        phrases=[
            "We found your profile on Naukri.com",           # 0 — distractor (sounds plausible)
            "work-from-home data entry role",                # 1 — distractor (legitimate roles exist)
            "earning ₹50,000 per month",                     # 2 ✓ REWARD / JOB_SCAM
            "No experience needed",                          # 3 ✓ JOB_SCAM (unrealistic promise)
            "registration fee of ₹999",                      # 4 ✓ MONEY_REQUEST
            "share your bank account details",               # 5 ✓ INFO_HARVEST / CREDENTIAL_REQUEST
            "full training provided",                        # 6 — distractor (normal job language)
            "Only 3 seats remaining — offer closes tonight", # 7 ✓ URGENCY + REWARD pressure
        ],
        correct_phrase_indices=[2, 3, 4, 5, 7],
        explanation=(
            "**Earning ₹50,000 per month / No experience needed** — Legitimate data-entry "
            "roles do not offer this salary without skills or experience. Unrealistic "
            "earnings promises are a hallmark of fake job scams.\n\n"
            "**Registration fee of ₹999** — Legitimate employers never charge you to join. "
            "Any upfront fee — however small — is a strong signal that this is a scam.\n\n"
            "**Share your bank account details** — Asking for banking information before any "
            "formal offer letter or employment contract is a serious red flag. "
            "This information can be used to drain your account or commit identity fraud.\n\n"
            "**Only 3 seats remaining — offer closes tonight** — Artificial scarcity and "
            "urgency are designed to stop you from researching the company or thinking critically. "
            "A real employer will not disappear if you take a day to verify."
        ),
        tactic_id="JOB_SCAM",
    ),
    DetectiveScenario(
        scenario_id="income_tax_scam",
        title="🏛️ Fake Income Tax / Government Notice Scam",
        message_text=(
            "NOTICE from Income Tax Department of India: "
            "A tax refund of ₹18,740 has been approved for PAN BXXXK1234F. "
            "To receive your refund, click: incometax-refund-claim.com "
            "Enter your bank account number, IFSC code, and Aadhaar OTP. "
            "Failure to claim within 48 hours will result in cancellation of your refund "
            "and a penalty notice."
        ),
        phrases=[
            "Income Tax Department of India",               # 0 ✓ AUTHORITY / IMPERSONATION
            "tax refund of ₹18,740",                        # 1 ✓ REWARD (too-good-to-be-true)
            "PAN BXXXK1234F",                               # 2 — distractor (generic PAN format)
            "incometax-refund-claim.com",                   # 3 ✓ SUSPICIOUS_LINK
            "bank account number, IFSC code, and Aadhaar OTP", # 4 ✓ CREDENTIAL_REQUEST
            "within 48 hours",                              # 5 ✓ URGENCY
            "cancellation of your refund",                  # 6 ✓ FEAR
            "penalty notice",                               # 7 ✓ FEAR
        ],
        correct_phrase_indices=[0, 1, 3, 4, 5, 6, 7],
        explanation=(
            "**Income Tax Department of India** — The real Income Tax Department does NOT "
            "send refund notices via SMS with a payment link. Official refunds are processed "
            "automatically to your registered bank account. Verify on incometaxindia.gov.in only.\n\n"
            "**Tax refund of ₹18,740** — An unexpected specific refund amount is designed to "
            "excite you into acting quickly. This is a reward/lure tactic.\n\n"
            "**incometax-refund-claim.com** — This is NOT the official incometaxindia.gov.in. "
            "The fake domain mimics official language to appear credible.\n\n"
            "**Bank account number, IFSC code, and Aadhaar OTP** — The government will NEVER "
            "ask for your Aadhaar OTP through a link. Sharing your OTP gives scammers "
            "immediate access to your account.\n\n"
            "**Within 48 hours / cancellation / penalty notice** — Multiple fear and urgency "
            "triggers appear together to overwhelm your judgment. Real tax refunds are not "
            "cancelled because you did not click a link."
        ),
        tactic_id="AUTHORITY",
    ),
]

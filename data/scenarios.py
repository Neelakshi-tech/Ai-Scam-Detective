"""Detective Mode sample scenarios.

Each DetectiveScenario contains:
  - A realistic (fictional) scam message
  - A list of selectable phrases shown to the user
  - The correct answers (indices into the phrases list)
  - An explanation revealed after submission
"""

from data.models import DetectiveScenario

SCENARIOS: list[DetectiveScenario] = [
    DetectiveScenario(
        scenario_id="parcel_delivery",
        title="🚚 Parcel Delivery Scam",
        message_text=(
            "Royal Mail: Your parcel could not be delivered today. "
            "A redelivery fee of £2.99 is required within 24 hours or your parcel "
            "will be returned to sender. Pay immediately at: royalm4il-delivery-fees.com. "
            "Failure to pay will result in a £15 storage charge."
        ),
        phrases=[
            "Royal Mail",                               # 0 — distractor (brand name, not itself suspicious)
            "redelivery fee of £2.99",                  # 1 ✓ MONEY_REQUEST
            "within 24 hours",                          # 2 ✓ URGENCY
            "parcel could not be delivered today",      # 3 — distractor (plausible statement)
            "royalm4il-delivery-fees.com",              # 4 ✓ SUSPICIOUS_LINK
            "returned to sender",                       # 5 — distractor (normal delivery term)
            "Failure to pay will result in a £15 storage charge",  # 6 ✓ FEAR
            "Pay immediately",                          # 7 ✓ URGENCY / MONEY_REQUEST
        ],
        correct_phrase_indices=[1, 2, 4, 6, 7],
        explanation=(
            "**Redelivery fee of £2.99** — Legitimate couriers do not request payment "
            "via a link in a text message. This is a money request tactic.\n\n"
            "**Within 24 hours / Pay immediately** — Creating artificial urgency stops "
            "you from thinking clearly and checking whether the message is real.\n\n"
            "**royalm4il-delivery-fees.com** — This domain uses the number '4' instead of "
            "the letter 'a' and is not the real Royal Mail website (royalmail.com). "
            "This is a fake domain designed to look real at a quick glance.\n\n"
            "**Failure to pay will result in a £15 storage charge** — This is a fear tactic. "
            "The threat of an escalating charge pressures you to act without questioning the message."
        ),
        tactic_id="MONEY_REQUEST",
    ),
    DetectiveScenario(
        scenario_id="fake_job_offer",
        title="💼 Fake Job Offer Scam",
        message_text=(
            "Hi! We found your CV on Indeed and would love to offer you a work-from-home position "
            "earning up to £800 per day. No experience needed — full training provided. "
            "To secure your spot, send a one-time registration fee of £49 via PayPal "
            "and provide your bank account details for payroll setup. Offer expires tonight!"
        ),
        phrases=[
            "We found your CV on Indeed",               # 0 — distractor (sounds plausible)
            "work-from-home position",                  # 1 — distractor (legitimate jobs exist)
            "earning up to £800 per day",               # 2 ✓ REWARD / JOB_SCAM
            "No experience needed",                     # 3 ✓ JOB_SCAM (unrealistic promise)
            "registration fee of £49",                  # 4 ✓ MONEY_REQUEST (paying to get a job)
            "bank account details for payroll setup",   # 5 ✓ INFO_HARVEST / CREDENTIAL_REQUEST
            "full training provided",                   # 6 — distractor (normal job offer language)
            "Offer expires tonight",                    # 7 ✓ URGENCY
        ],
        correct_phrase_indices=[2, 3, 4, 5, 7],
        explanation=(
            "**Earning up to £800 per day / No experience needed** — Unrealistic salary promises "
            "with no required skills are a classic sign of a fake job scam.\n\n"
            "**Registration fee of £49** — Legitimate employers never charge you to start a job. "
            "Any upfront fee is a strong signal this is a scam.\n\n"
            "**Bank account details for payroll setup** — Asking for banking credentials before "
            "any formal employment contract is highly suspicious and risky.\n\n"
            "**Offer expires tonight** — Manufactured urgency prevents you from researching "
            "the company or taking time to think critically."
        ),
        tactic_id="JOB_SCAM",
    ),
    DetectiveScenario(
        scenario_id="bank_impersonation",
        title="🏦 Bank Impersonation Scam",
        message_text=(
            "URGENT: Barclays Security Team — Unusual activity has been detected on your account. "
            "Your account has been temporarily suspended to protect you. "
            "To restore access, verify your identity at: barclays-secure-verify.net "
            "You will need your card number, PIN, and the one-time passcode sent to your phone. "
            "If you do not verify within 2 hours your account will be permanently closed."
        ),
        phrases=[
            "Barclays Security Team",                              # 0 ✓ IMPERSONATION / AUTHORITY
            "Unusual activity has been detected",                  # 1 ✓ FEAR
            "account has been temporarily suspended",              # 2 ✓ FEAR
            "To restore access",                                   # 3 — distractor (sounds reasonable)
            "barclays-secure-verify.net",                          # 4 ✓ SUSPICIOUS_LINK
            "card number, PIN, and the one-time passcode",         # 5 ✓ CREDENTIAL_REQUEST
            "sent to your phone",                                  # 6 — distractor (normal OTP description)
            "account will be permanently closed",                  # 7 ✓ FEAR / URGENCY
            "within 2 hours",                                      # 8 ✓ URGENCY
        ],
        correct_phrase_indices=[0, 1, 2, 4, 5, 7, 8],
        explanation=(
            "**Barclays Security Team** — Scammers impersonate trusted banks to seem legitimate. "
            "The name of a real bank in a message does not make that message real.\n\n"
            "**Unusual activity / account suspended** — Fear tactics are designed to make you "
            "act without thinking. Real banks contact you through secure in-app messages or post.\n\n"
            "**barclays-secure-verify.net** — This is NOT barclays.co.uk. "
            "The fake domain looks similar but leads to a phishing website.\n\n"
            "**Card number, PIN, and one-time passcode** — Your bank will NEVER ask for your PIN "
            "or one-time passcode. Anyone asking for these is trying to steal your account.\n\n"
            "**Permanently closed / within 2 hours** — Extreme consequences with a tight deadline "
            "are designed to panic you into complying immediately."
        ),
        tactic_id="CREDENTIAL_REQUEST",
    ),
]

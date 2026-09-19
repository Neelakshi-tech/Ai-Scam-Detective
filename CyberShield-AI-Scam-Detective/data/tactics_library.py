"""Static tactic library for the Learn section.

Each entry maps a tactic ID to a dict with:
  - name:        Human-readable tactic name
  - icon:        Emoji used in the UI
  - description: What this tactic is and how scammers use it
  - example:     A concrete example of the tactic in a message
  - warning:     Specific warning signs to watch for
  - tip:         Safe action the user should take
"""

TACTICS_LIBRARY: dict[str, dict] = {
    "URGENCY": {
        "name": "Urgency / Time Pressure",
        "icon": "⏰",
        "description": (
            "Scammers create a false sense of urgency to stop you from "
            "thinking clearly. By forcing a rushed decision, they hope you "
            "will act before you have time to question whether the message is real."
        ),
        "example": (
            '"Your account will be closed in 24 hours unless you verify immediately." '
            "The real company almost never sets such tight deadlines via text or email."
        ),
        "warning": (
            "Words like 'Act now', 'Expires today', 'Last chance', 'Immediate action required', "
            "or countdown timers are strong urgency signals."
        ),
        "tip": (
            "Slow down. Legitimate organisations give you reasonable time to respond. "
            "Contact the organisation directly through their official website — not a link in the message."
        ),
    },
    "FEAR": {
        "name": "Fear or Threat",
        "icon": "😨",
        "description": (
            "Scammers use fear and threats to cloud your judgment. "
            "Threatening legal action, account suspension, arrest, or financial loss "
            "makes victims comply quickly without verifying the claim."
        ),
        "example": (
            '"Failure to respond will result in legal proceedings and a fine of £500." '
            "Real authorities send formal written notices — not unexpected texts or emails."
        ),
        "warning": (
            "Phrases like 'Legal action', 'Your account will be suspended', "
            "'Warrant for your arrest', or 'Final warning' are common fear tactics."
        ),
        "tip": (
            "Do not panic. If you receive a threatening message, verify it independently "
            "by calling the official number of the organisation — found on their real website, not in the message."
        ),
    },
    "AUTHORITY": {
        "name": "Fake Authority",
        "icon": "🏛️",
        "description": (
            "Scammers impersonate trusted organisations such as banks, government agencies, "
            "police, or courts to add false credibility to their request. "
            "The name of a real institution does not make a message legitimate."
        ),
        "example": (
            '"This is HMRC. You have an unpaid tax refund. Click here to claim it." '
            "Government agencies communicate through official post, not unsolicited texts."
        ),
        "warning": (
            "Unsolicited contact claiming to be from HMRC, IRS, police, banks, courts, "
            "or well-known companies — especially requesting urgent action or payment."
        ),
        "tip": (
            "Always verify by contacting the organisation directly using a number or address "
            "from their official website. Never use contact details supplied in the suspicious message."
        ),
    },
    "MONEY_REQUEST": {
        "name": "Request for Money or Payment",
        "icon": "💸",
        "description": (
            "Many scams ultimately aim to extract money. "
            "Payment may be requested via bank transfer, gift cards, cryptocurrency, "
            "or small 'processing fees' that seem harmless but are fraudulent."
        ),
        "example": (
            '"Pay £2.99 to release your parcel." '
            "Legitimate delivery services do not request payment via a link in a text message."
        ),
        "warning": (
            "Any unexpected payment request — however small — especially via gift cards, "
            "cryptocurrency, wire transfer, or an unfamiliar payment link."
        ),
        "tip": (
            "Never pay in response to an unsolicited message. "
            "Verify the request through the organisation's official channels before sending any money."
        ),
    },
    "CREDENTIAL_REQUEST": {
        "name": "Request for Passwords or Credentials",
        "icon": "🔑",
        "description": (
            "Phishing scams trick users into handing over passwords, PINs, OTPs, "
            "or account credentials. These are then used to access accounts, "
            "commit fraud, or be sold on the dark web."
        ),
        "example": (
            '"Please confirm your online banking password and the OTP sent to your phone." '
            "No legitimate bank will ever ask for your full password or OTP."
        ),
        "warning": (
            "Any request for a password, PIN, one-time passcode, security question answer, "
            "or login credentials — through any channel."
        ),
        "tip": (
            "Never share your password, PIN, or OTP with anyone, for any reason. "
            "Genuine organisations will never ask for these details."
        ),
    },
    "SUSPICIOUS_LINK": {
        "name": "Suspicious Link or Domain",
        "icon": "🔗",
        "description": (
            "Fraudulent links look convincing but lead to fake websites designed to "
            "steal your credentials or install malware. Scammers use misspelled domain names, "
            "unusual extensions, or long URLs to disguise fake sites."
        ),
        "example": (
            '"Click here: royalm4il-delivery.com" — notice the number 4 replacing the letter A, '
            "and an unofficial domain rather than the real royalmail.com."
        ),
        "warning": (
            "Links with misspellings, extra words, unusual domains (.xyz, .tk, .info), "
            "or long strings of characters. If the URL looks even slightly 'off', it is a red flag."
        ),
        "tip": (
            "Do not click links in unexpected messages. "
            "Instead, go directly to the organisation's website by typing the address yourself."
        ),
    },
    "REWARD": {
        "name": "Unrealistic Reward or Offer",
        "icon": "🎁",
        "description": (
            "Scammers promise prizes, lottery wins, cashback, or investment returns "
            "that are too good to be true. The goal is to excite the victim "
            "into acting quickly before they question the legitimacy of the offer."
        ),
        "example": (
            '"Congratulations! You have won a £5,000 Amazon voucher. Claim now." '
            "You cannot win a prize from a competition you did not enter."
        ),
        "warning": (
            "Unexpected prize wins, guaranteed returns on investments, "
            "free gifts requiring only 'a small fee', or exclusive offers with no clear origin."
        ),
        "tip": (
            "If it sounds too good to be true, it almost certainly is. "
            "Research the claimed competition or offer independently before taking any action."
        ),
    },
    "JOB_SCAM": {
        "name": "Fake Job or Investment Opportunity",
        "icon": "💼",
        "description": (
            "Fake job offers and investment schemes promise easy money for little effort. "
            "Victims may be asked to pay an upfront 'registration fee', "
            "provide bank details for payroll, or recruit others into the scheme."
        ),
        "example": (
            '"Work from home, earn £800/day — no experience required. '
            'Pay a £49 registration fee to secure your place." '
            "Legitimate employers never charge you to start a job."
        ),
        "warning": (
            "Jobs with unrealistic salaries, upfront fees, requests for bank details before starting, "
            "or vague descriptions like 'data entry' or 'package forwarding'."
        ),
        "tip": (
            "Research the company independently. "
            "Never pay money to get a job, and never share bank details before formal employment paperwork."
        ),
    },
    "IMPERSONATION": {
        "name": "Impersonation",
        "icon": "🎭",
        "description": (
            "Scammers pose as a trusted person or organisation — a bank, a delivery company, "
            "a government body, a friend, or even a family member. "
            "The fake identity makes the request seem credible."
        ),
        "example": (
            '"Hi Mum, I lost my phone and need you to send £200 urgently — it\'s me, Jamie." '
            "Always verify unexpected requests from known contacts through a different channel."
        ),
        "warning": (
            "Contact from a familiar name or brand, especially with an urgent request, "
            "using a number or email you do not recognise."
        ),
        "tip": (
            "If you receive an unexpected request from someone claiming to be a person or organisation "
            "you trust, verify it directly through an official or known contact method — not the one in the message."
        ),
    },
    "INFO_HARVEST": {
        "name": "Personal Information Harvesting",
        "icon": "📋",
        "description": (
            "Some scams collect personal details — name, address, date of birth, National Insurance number — "
            "to commit identity fraud or to make future scam attempts more convincing and personalised."
        ),
        "example": (
            '"To claim your prize, reply with your full name, date of birth, and home address." '
            "This information can be used for identity theft."
        ),
        "warning": (
            "Requests for personal details you would not normally share — especially date of birth, "
            "address, National Insurance or Social Security number, or passport details."
        ),
        "tip": (
            "Never share personal information in response to an unsolicited message. "
            "Legitimate prize claims use formal verification processes, not a quick text reply."
        ),
    },
}

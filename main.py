# ============================================================
# AI TRAVEL ASSISTANT - VERSION 5
# ============================================================

from google import genai
from dotenv import load_dotenv
import streamlit as st
from datetime import date
import io
import os

# PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# STREAMLIT PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="AI Travel Assistant",
    page_icon="✈️",
    layout="centered"
)


# ============================================================
# CSS / YOUR ORIGINAL DESIGN
# ============================================================

st.markdown("""
<style>

/* ===== BACKGROUND ===== */

.stApp {
    background:
        linear-gradient(
            rgba(0,0,0,0.25),
            rgba(0,0,0,0.35)
        ),
        url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e");

    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}


/* ===== TITLE ===== */

h1 {
    color: white !important;
    text-align: center;
    font-size: 42px !important;
    text-shadow: 0 3px 15px rgba(0,0,0,0.6);
}

h2, h3 {
    color: white !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}

p, label {
    color: white !important;
}


/* ===== ALL INPUT BOXES ===== */

.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stDateInput input,
.stMultiSelect div[data-baseweb="select"] > div,
.stTextArea textarea {

    background: rgba(0,0,0,0.45) !important;

    color: white !important;

    border: 1px solid rgba(255,255,255,0.25) !important;

    border-radius: 12px !important;

    backdrop-filter: blur(10px);
}


/* Input text */

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTextArea textarea {
    color: white !important;
}


/* Placeholder */

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: rgba(255,255,255,0.65) !important;
}


/* Selectbox text */

.stSelectbox div[data-baseweb="select"] span,
.stMultiSelect div[data-baseweb="select"] span {
    color: white !important;
}


/* ===== DROPDOWN ===== */

div[data-baseweb="popover"] {
    background: rgba(20,20,20,0.95) !important;
}

div[data-baseweb="menu"] {
    background: rgba(20,20,20,0.95) !important;
}

div[data-baseweb="menu"] li {
    color: white !important;
}

div[data-baseweb="menu"] li:hover {
    background: rgba(255,255,255,0.15) !important;
}


/* ===== BUTTON ===== */

.stButton > button {

    width: 100%;

    background: rgba(0,120,200,0.75) !important;

    color: white !important;

    border: 1px solid rgba(255,255,255,0.25) !important;

    border-radius: 12px !important;

    font-size: 16px !important;
    font-weight: 600 !important;

    padding: 12px !important;

    backdrop-filter: blur(10px);

    transition: 0.2s;
}


/* Button hover */

.stButton > button:hover {
    background: rgba(0,150,220,0.9) !important;
    transform: translateY(-2px);
}


/* ===== SUCCESS / WARNING / INFO ===== */

div[data-testid="stAlert"] {
    background: rgba(0,0,0,0.45) !important;
    backdrop-filter: blur(10px);
    border-radius: 12px !important;
}


/* ===== EXPANDER ===== */

div[data-testid="stExpander"] {
    background: rgba(0,0,0,0.35) !important;
    border: 1px solid rgba(255,255,255,0.20) !important;
    border-radius: 12px !important;
}


/* ===== CAPTION ===== */

[data-testid="stCaptionContainer"] {
    color: rgba(255,255,255,0.85) !important;
    text-align: center;
}


/* ===== DIVIDER ===== */

hr {
    border-color: rgba(255,255,255,0.20) !important;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# GEMINI CLIENT
# ============================================================

try:
    client = genai.Client()
    gemini_available = True
except Exception:
    client = None
    gemini_available = False


# ============================================================
# SESSION STATE
# ============================================================

if "trip_plan" not in st.session_state:
    st.session_state.trip_plan = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "saved_trips" not in st.session_state:
    st.session_state.saved_trips = []

if "trip_generated" not in st.session_state:
    st.session_state.trip_generated = False


# ============================================================
# PDF GENERATOR
# ============================================================

def create_pdf(text, destination):

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    body_style = styles["BodyText"]

    story = []

    story.append(
        Paragraph(
            f"✈️ AI Travel Plan - {destination}",
            title_style
        )
    )

    story.append(Spacer(1, 20))

    # Convert plain text into PDF paragraphs
    for line in text.split("\n"):

        if line.strip():

            safe_line = (
                line
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            story.append(
                Paragraph(
                    safe_line,
                    body_style
                )
            )

            story.append(Spacer(1, 6))

    document.build(story)

    buffer.seek(0)

    return buffer


# ============================================================
# HEADER
# ============================================================

st.title("🌍✈️ Travel Assistant 🌏✈️")

st.caption("Your Personal AI Trip Planner")


# ============================================================
# API STATUS
# ============================================================

if not gemini_available:
    st.warning(
        "⚠️ Gemini could not be initialized. "
        "Check your GEMINI_API_KEY in the .env file."
    )


# ============================================================
# TRIP DETAILS
# ============================================================

st.subheader("🌍 Plan Your Trip")

destination = st.text_input(
    "Where do you wanna go buddy...😃?",
    placeholder="Example: Goa, Paris, Dubai..."
)

col1, col2 = st.columns(2)

with col1:

    start_date = st.date_input(
        "📅 Starting Date",
        value=date.today()
    )

with col2:

    days = st.number_input(
        "🗓️ How many days of trip?",
        min_value=1,
        max_value=365,
        value=5
    )


# ============================================================
# BUDGET
# ============================================================

st.subheader("💰 Budget")

col1, col2 = st.columns(2)

with col1:

    budget = st.number_input(
        "What is your budget...💵?",
        min_value=5000,
        max_value=2000000,
        value=50000,
        step=1000
    )

with col2:

    budget_type = st.selectbox(
        "Budget Type",
        [
            "Total trip budget",
            "Budget per person"
        ]
    )


# ============================================================
# TRAVELLERS
# ============================================================

st.subheader("👥 Travellers")

col1, col2 = st.columns(2)

with col1:

    travel_type = st.selectbox(
        "Whom You're Travelling With...?",
        [
            "Family",
            "Solo",
            "Friends",
            "Couple"
        ]
    )

with col2:

    travellers = st.number_input(
        "Number of Travellers",
        min_value=1,
        max_value=50,
        value=1
    )


# ============================================================
# PREFERENCES
# ============================================================

st.subheader("🎯 Your Preferences")

interests = st.multiselect(
    "What are you interested in?",
    [
        "🏖️ Beaches",
        "🏔️ Mountains",
        "🌲 Nature",
        "🏛️ History",
        "🛕 Culture",
        "🍛 Food",
        "🛍️ Shopping",
        "🎢 Adventure",
        "📸 Photography",
        "🌃 Nightlife",
        "🧘 Relaxation"
    ],
    default=["🌲 Nature"]
)


col1, col2 = st.columns(2)

with col1:

    hotel_preference = st.selectbox(
        "🏨 Hotel Preference",
        [
            "Budget",
            "Standard",
            "Premium",
            "Luxury"
        ]
    )

with col2:

    transport_preference = st.selectbox(
        "🚗 Transportation Preference",
        [
            "Public transport",
            "Train",
            "Bus",
            "Car",
            "Taxi",
            "Flight where necessary"
        ]
    )


food_preference = st.selectbox(
    "🍛 Food Preference",
    [
        "Vegetarian",
        "Non-vegetarian",
        "Both",
        "No preference"
    ]
)


trip_style = st.selectbox(
    "✨ What type of trip do you want?",
    [
        "Balanced",
        "Relaxing",
        "Adventure",
        "Budget",
        "Luxury",
        "Backpacking",
        "Photography",
        "Family-friendly"
    ]
)


# ============================================================
# EXTRA REQUEST
# ============================================================

extra_request = st.text_area(
    "💬 Anything else you want?",
    placeholder=(
        "Example: I don't want too much walking, "
        "I want to visit famous food places..."
    )
)


# ============================================================
# PLAN TRIP
# ============================================================

if st.button("✈️ Plan My Trip"):

    if not destination.strip():

        st.warning(
            "Please enter your destination first 😃"
        )

    elif not gemini_available:

        st.error(
            "Gemini is not available. "
            "Please check your API key."
        )

    else:

        interests_text = ", ".join(interests)

        query = f"""
Create a detailed travel itinerary using the following information.

DESTINATION:
{destination}

START DATE:
{start_date}

NUMBER OF DAYS:
{days}

BUDGET:
₹{budget}

BUDGET TYPE:
{budget_type}

TRAVELLING WITH:
{travel_type}

NUMBER OF TRAVELLERS:
{travellers}

INTERESTS:
{interests_text}

HOTEL PREFERENCE:
{hotel_preference}

TRANSPORTATION:
{transport_preference}

FOOD PREFERENCE:
{food_preference}

TRIP STYLE:
{trip_style}

EXTRA REQUEST:
{extra_request}

Create a practical and realistic travel plan.

Structure your response as:

🌍 TRIP OVERVIEW

📅 DAY-BY-DAY ITINERARY

For every day include:
• Morning
• Afternoon
• Evening

🏨 STAY

Suggest the best area/type of accommodation.

🍛 FOOD

Mention local foods or cuisine worth trying.

🚗 TRANSPORTATION

Explain how the traveller can move around.

💰 BUDGET BREAKDOWN

Give approximate amounts for:
• Accommodation
• Food
• Transportation
• Activities
• Miscellaneous

🎒 THINGS TO PACK

⚠️ IMPORTANT TRAVEL TIPS

⭐ SPECIAL RECOMMENDATIONS

Do not invent exact live prices, hotel availability,
weather conditions, or transport schedules.
Clearly mark estimates as estimates.
Keep the answer practical and easy to follow.
Use emojis naturally.
"""

        try:

            with st.spinner(
                "✈️ Your AI travel agent is preparing your trip..."
            ):

                interaction = client.interactions.create(
                    model="gemini-3.5-flash-lite",
                    input=query,
                    system_instruction="""
You are an expert and experienced travel agent and manager.

Whenever the user asks questions related to travel or trip
planning, provide detailed, practical and organized answers.

Use bullet points and clear sections.

Interact with the user in polite, playful and friendly language.

If the user tells you about themselves, ask only one useful
question at a time instead of asking many questions.

Do not repeatedly greet the user.

Use emojis naturally to make the conversation immersive.

Never pretend that you have live information if you do not have it.
Clearly distinguish estimates from confirmed information.
""",
                    generation_config={
                        "temperature": 1,
                        "top_k": 100,
                        "max_output_tokens": 1500,
                    }
                )

            result = interaction.output_text

            st.session_state.trip_plan = result
            st.session_state.trip_generated = True

            # Save current trip information
            st.session_state.saved_trips.append({
                "destination": destination,
                "date": str(start_date),
                "days": days,
                "budget": budget,
                "travel_type": travel_type
            })

            st.session_state.chat_history = []

        except Exception as e:

            st.error(
                f"❌ Gemini error: {str(e)}"
            )


# ============================================================
# DISPLAY TRIP PLAN
# ============================================================

if st.session_state.trip_plan:

    st.divider()

    st.subheader(
        f"🌍 Your {destination} Travel Plan"
    )

    st.markdown(
        st.session_state.trip_plan
    )

    st.divider()

    # ========================================================
    # DOWNLOAD PDF
    # ========================================================

    pdf_file = create_pdf(
        st.session_state.trip_plan,
        destination
    )

    st.download_button(
        label="📄 Download Trip as PDF",
        data=pdf_file,
        file_name=f"{destination}_travel_plan.pdf",
        mime="application/pdf"
    )

    # ========================================================
    # GOOGLE MAPS
    # ========================================================

    maps_url = (
        "https://www.google.com/maps/search/"
        + destination.replace(" ", "+")
    )

    st.link_button(
        "🗺️ Open Destination in Google Maps",
        maps_url
    )

    # ========================================================
    # REGENERATE
    # ========================================================

    if st.button("🔄 Generate Another Plan"):

        if gemini_available:

            regenerate_prompt = f"""
Create a DIFFERENT travel itinerary for:

Destination: {destination}
Days: {days}
Budget: ₹{budget}
Travelling with: {travel_type}
Interests: {", ".join(interests)}
Hotel: {hotel_preference}
Transport: {transport_preference}
Food: {food_preference}
Style: {trip_style}

Create a different itinerary from the previous one.
Focus on different places and activities where practical.
Keep the budget in mind.
"""

            try:

                with st.spinner(
                    "🔄 Creating another itinerary..."
                ):

                    interaction = client.interactions.create(
                        model="gemini-3.5-flash-lite",
                        input=regenerate_prompt,
                        system_instruction="""
You are a professional travel planner.
Create practical alternative itineraries.
Use clear sections, bullet points and emojis.
Do not claim live information that you cannot verify.
""",
                        generation_config={
                            "temperature": 1.2,
                            "top_k": 100,
                            "max_output_tokens": 1500,
                        }
                    )

                st.session_state.trip_plan = (
                    interaction.output_text
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not regenerate plan: {str(e)}"
                )


# ============================================================
# AI FOLLOW-UP CHAT
# ============================================================

if st.session_state.trip_plan:

    st.divider()

    st.subheader(
        "💬 Ask Your Travel Assistant"
    )

    st.caption(
        "Ask anything about your generated trip."
    )

    user_question = st.chat_input(
        "Example: Make Day 2 cheaper..."
    )

    if user_question:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": user_question
            }
        )

        conversation = ""

        for message in st.session_state.chat_history:

            conversation += (
                f"{message['role'].upper()}: "
                f"{message['content']}\n"
            )

        chat_prompt = f"""
You are continuing a travel planning conversation.

CURRENT TRIP PLAN:

{st.session_state.trip_plan}

CONVERSATION:

{conversation}

Answer the user's latest question.

Keep the answer practical and connected to the trip.
If they ask to change something, provide the revised suggestion.
Do not invent live information.
"""

        if gemini_available:

            try:

                with st.spinner("🤖 Thinking..."):

                    interaction = client.interactions.create(
                        model="gemini-3.5-flash-lite",
                        input=chat_prompt,
                        system_instruction="""
You are a friendly AI travel assistant.
Give concise but useful answers.
Use bullet points when appropriate.
Keep the conversation natural.
""",
                        generation_config={
                            "temperature": 1,
                            "top_k": 100,
                            "max_output_tokens": 800,
                        }
                    )

                answer = interaction.output_text

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

            except Exception as e:

                st.error(
                    f"Chat error: {str(e)}"
                )


# ============================================================
# SHOW CHAT HISTORY
# ============================================================

if st.session_state.chat_history:

    st.divider()

    st.subheader("💬 Conversation")

    for message in st.session_state.chat_history:

        if message["role"] == "user":

            with st.chat_message("user"):
                st.write(message["content"])

        else:

            with st.chat_message("assistant"):
                st.write(message["content"])


# ============================================================
# SAVED TRIPS
# ============================================================

if st.session_state.saved_trips:

    st.divider()

    with st.expander("💾 Saved Trips"):

        for index, trip in enumerate(
            reversed(st.session_state.saved_trips),
            start=1
        ):

            st.write(
                f"""
                **Trip {index}**

                🌍 Destination: {trip['destination']}

                📅 Date: {trip['date']}

                🗓️ Days: {trip['days']}

                💰 Budget: ₹{trip['budget']}

                👥 Travelling with: {trip['travel_type']}
                """
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption( "🌍 AI Travel Assistant • Plan smarter • Travel better ✈️")
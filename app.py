from enum import StrEnum

import streamlit as st
from langchain_core.messages import HumanMessage, trim_messages
from langchain_google_genai import ChatGoogleGenerativeAI


class Actor(StrEnum):
    AI = "ai"
    HUMAN = "user"


MAX_TOKENS = 200
MODEL_NAME = "gemini-2.0-flash"
USER_MSG_KEY = "umsgs"
TRIMMED_MSG_KEY = "trmd_msgs"

st.title("💬 Chatty")
api_key = st.sidebar.text_input("Gemini API Key", icon="🔑")

# https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
if USER_MSG_KEY not in st.session_state:
    st.session_state[USER_MSG_KEY] = []

if TRIMMED_MSG_KEY not in st.session_state:
    st.session_state[TRIMMED_MSG_KEY] = []


# https://docs.streamlit.io/develop/concepts/architecture/caching
@st.cache_resource
def get_model(api_key: str):
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=api_key,
    )


@st.cache_resource
def get_trimmer(_model: ChatGoogleGenerativeAI):
    # https://python.langchain.com/docs/tutorials/chatbot/#managing-conversation-history
    # `_model`` is to avoid streamlit hash the arg; else it throws error idk why.
    return trim_messages(
        max_tokens=MAX_TOKENS,
        strategy="last",
        token_counter=_model,  # using model is taking a lot of time, idk why.
        include_system=True,
        start_on="human",
    )


def render_responses():
    for msg in st.session_state[USER_MSG_KEY]:
        actor = Actor.HUMAN if isinstance(msg, HumanMessage) else Actor.AI
        with st.chat_message(name=actor):
            st.write(msg.content)

        # Local LLMs show these token stats data then
        # why not add in web apps if gemini API provides? ¯\_(ツ)_/¯
        if actor is Actor.AI:
            input_tokens = msg.usage_metadata.get("input_tokens", -1)
            output_tokens = msg.usage_metadata.get("output_tokens", -1)
            st.markdown(
                f":green-badge[input tokens: {input_tokens}] :blue-badge[output tokens: {output_tokens}]"
            )


model = None
if api_key and api_key.strip():
    model = get_model(api_key)
else:
    st.info("Enter the GEMINI_API_KEY to get started.")
    # raise ValueError("GEMINI_API_KEY is missing.")
    # Earlier due to the streamlit execution flow, its not feasible to halt a running program, I was throwing exceptions but I found a better solution for a better UX


user_prompt = st.chat_input(
    placeholder="Express yourself through the combinations of alphabets!"
)  # removed default AI msg; so idk what better to put as placeholder :/

if user_prompt and model:
    st.session_state[USER_MSG_KEY].append(HumanMessage(content=user_prompt))
    st.session_state[TRIMMED_MSG_KEY].append(HumanMessage(content=user_prompt))

    with st.status("Trimming messages...") as status:
        old_trimmed_msgs = st.session_state[TRIMMED_MSG_KEY]
        # print(f"old_trimmed_msgs: {len(old_trimmed_msgs)}")

        trimmer = get_trimmer(_model=model)
        new_trimmed_msgs = trimmer.invoke(old_trimmed_msgs)
        # print(f"new_trimmed_msgs: {len(new_trimmed_msgs)}")

        st.session_state[TRIMMED_MSG_KEY] = new_trimmed_msgs

        if len(old_trimmed_msgs) != len(new_trimmed_msgs):
            status.update(
                label=f"Reduced total messages from {len(old_trimmed_msgs)} to {len(new_trimmed_msgs)} (max tokens: {MAX_TOKENS})"
            )
        else:
            status.update(label="Trimmed messages.")

    with st.status("Processing your query...") as status:
        resp = model.invoke(st.session_state[TRIMMED_MSG_KEY])

        st.session_state[USER_MSG_KEY].append(resp)
        st.session_state[TRIMMED_MSG_KEY].append(resp)

        status.update(label="Finished processing your query.")

    render_responses()

"""
Streamlit Web Application for Chakravyuha Simulation Visualization.
"""

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Chakravyuha Multi-Agent Simulation", layout="wide")
    st.title("🛡️ Chakravyuha Simulation")
    st.subheader("Multi-Agent Coordination Under Incomplete Information (Drona Parva)")
    st.info("Simulation interface initialized. Configuration parameters and visual canvas will appear here.")


if __name__ == "__main__":
    main()

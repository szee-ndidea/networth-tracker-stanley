import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Net Worth Tracker", page_icon="💰", layout="wide")

st.title("Net Worth Tracker")
st.caption("Track assets, debts, and net worth over time.")


def init_state():
    if "asset_categories" not in st.session_state:
        st.session_state.asset_categories = [
            "Cash",
            "Checking",
            "Savings",
            "Brokerage",
            "Retirement",
            "Real Estate",
            "Crypto",
            "Other",
        ]

    if "debt_categories" not in st.session_state:
        st.session_state.debt_categories = [
            "Credit Card",
            "Student Loan",
            "Mortgage",
            "Auto Loan",
            "Personal Loan",
            "Tax Debt",
            "Other",
        ]

    if "asset_entries" not in st.session_state:
        st.session_state.asset_entries = []

    if "debt_entries" not in st.session_state:
        st.session_state.debt_entries = []


init_state()


with st.sidebar:
    st.header("Manage Categories")

    st.subheader("Add Asset Category")
    new_asset_category = st.text_input("New asset category", key="new_asset_category")
    if st.button("Add asset category"):
        value = new_asset_category.strip()
        if value and value not in st.session_state.asset_categories:
            st.session_state.asset_categories.append(value)
            st.success(f'Added asset category: {value}')
        elif value:
            st.warning("That asset category already exists.")

    st.subheader("Add Debt Category")
    new_debt_category = st.text_input("New debt category", key="new_debt_category")
    if st.button("Add debt category"):
        value = new_debt_category.strip()
        if value and value not in st.session_state.debt_categories:
            st.session_state.debt_categories.append(value)
            st.success(f'Added debt category: {value}')
        elif value:
            st.warning("That debt category already exists.")

    st.divider()
    st.write("**Current asset categories**")
    st.write(", ".join(st.session_state.asset_categories))

    st.write("**Current debt categories**")
    st.write(", ".join(st.session_state.debt_categories))


asset_tab, debt_tab, summary_tab = st.tabs(["Assets", "Debts", "Summary"])


with asset_tab:
    st.subheader("Assets")

    with st.form("asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            asset_date = st.date_input("Date", value=date.today(), key="asset_date")
            asset_name = st.text_input("Asset name", placeholder="Example: Fidelity 401(k)")
            asset_category = st.selectbox("Category", st.session_state.asset_categories)
        with col2:
            asset_value = st.number_input("Value", min_value=0.0, step=100.0, format="%.2f")
            asset_notes = st.text_input("Notes", placeholder="Optional")

        add_asset = st.form_submit_button("Add asset entry")
        if add_asset:
            if asset_name.strip():
                st.session_state.asset_entries.append(
                    {
                        "Date": pd.to_datetime(asset_date),
                        "Name": asset_name.strip(),
                        "Category": asset_category,
                        "Value": float(asset_value),
                        "Notes": asset_notes.strip(),
                    }
                )
                st.success("Asset entry added.")
            else:
                st.error("Please enter an asset name.")

    if st.session_state.asset_entries:
        asset_df = pd.DataFrame(st.session_state.asset_entries).sort_values(
            by=["Date", "Category", "Name"], ascending=[False, True, True]
        )
        st.dataframe(asset_df, use_container_width=True, hide_index=True)
    else:
        st.info("No asset entries yet.")


with debt_tab:
    st.subheader("Debts")

    with st.form("debt_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            debt_date = st.date_input("Date", value=date.today(), key="debt_date")
            debt_name = st.text_input("Debt name", placeholder="Example: Chase Visa")
            debt_category = st.selectbox("Category", st.session_state.debt_categories)
        with col2:
            debt_value = st.number_input("Balance", min_value=0.0, step=100.0, format="%.2f")
            debt_notes = st.text_input("Notes", placeholder="Optional")

        add_debt = st.form_submit_button("Add debt entry")
        if add_debt:
            if debt_name.strip():
                st.session_state.debt_entries.append(
                    {
                        "Date": pd.to_datetime(debt_date),
                        "Name": debt_name.strip(),
                        "Category": debt_category,
                        "Balance": float(debt_value),
                        "Notes": debt_notes.strip(),
                    }
                )
                st.success("Debt entry added.")
            else:
                st.error("Please enter a debt name.")

    if st.session_state.debt_entries:
        debt_df = pd.DataFrame(st.session_state.debt_entries).sort_values(
            by=["Date", "Category", "Name"], ascending=[False, True, True]
        )
        st.dataframe(debt_df, use_container_width=True, hide_index=True)
    else:
        st.info("No debt entries yet.")


with summary_tab:
    st.subheader("Summary")

    asset_df = pd.DataFrame(st.session_state.asset_entries) if st.session_state.asset_entries else pd.DataFrame(
        columns=["Date", "Name", "Category", "Value", "Notes"]
    )
    debt_df = pd.DataFrame(st.session_state.debt_entries) if st.session_state.debt_entries else pd.DataFrame(
        columns=["Date", "Name", "Category", "Balance", "Notes"]
    )

    total_assets = float(asset_df["Value"].sum()) if not asset_df.empty else 0.0
    total_debts = float(debt_df["Balance"].sum()) if not debt_df.empty else 0.0
    net_worth = total_assets - total_debts

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Assets", f"${total_assets:,.2f}")
    col2.metric("Total Debts", f"${total_debts:,.2f}")
    col3.metric("Net Worth", f"${net_worth:,.2f}")

    st.markdown("### Snapshot by Date")

    all_dates = sorted(
        set(asset_df["Date"].dt.date.tolist() if not asset_df.empty else [])
        | set(debt_df["Date"].dt.date.tolist() if not debt_df.empty else []),
        reverse=True,
    )

    if all_dates:
        selected_date = st.selectbox("Choose a date", all_dates)

        assets_on_date = asset_df[asset_df["Date"].dt.date == selected_date] if not asset_df.empty else pd.DataFrame()
        debts_on_date = debt_df[debt_df["Date"].dt.date == selected_date] if not debt_df.empty else pd.DataFrame()

        assets_value = float(assets_on_date["Value"].sum()) if not assets_on_date.empty else 0.0
        debts_value = float(debts_on_date["Balance"].sum()) if not debts_on_date.empty else 0.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Assets on selected date", f"${assets_value:,.2f}")
        c2.metric("Debts on selected date", f"${debts_value:,.2f}")
        c3.metric("Net worth on selected date", f"${assets_value - debts_value:,.2f}")

        if not assets_on_date.empty:
            st.markdown("**Assets on selected date**")
            st.dataframe(assets_on_date.sort_values(by=["Category", "Name"]), use_container_width=True, hide_index=True)

        if not debts_on_date.empty:
            st.markdown("**Debts on selected date**")
            st.dataframe(debts_on_date.sort_values(by=["Category", "Name"]), use_container_width=True, hide_index=True)
    else:
        st.info("Add at least one asset or debt entry to view summaries by date.")

    st.markdown("### Export Data")
    if not asset_df.empty:
        st.download_button(
            "Download asset data as CSV",
            data=asset_df.to_csv(index=False),
            file_name="asset_entries.csv",
            mime="text/csv",
        )

    if not debt_df.empty:
        st.download_button(
            "Download debt data as CSV",
            data=debt_df.to_csv(index=False),
            file_name="debt_entries.csv",
            mime="text/csv",
        )


st.divider()
st.caption("Prototype version: session-based data only. Closing or refreshing the app will clear entries unless you add file or database storage.")

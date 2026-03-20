import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Net Worth Tracker", page_icon="💰", layout="wide")

st.title("Net Worth Tracker")
st.caption("Track accounts, balances, and net worth over time.")


def init_state():
    if "asset_types" not in st.session_state:
        st.session_state.asset_types = [
            "Cash",
            "Checking",
            "Savings",
            "Brokerage",
            "Retirement",
            "Real Estate",
            "Crypto",
            "Other",
        ]

    if "debt_types" not in st.session_state:
        st.session_state.debt_types = [
            "Credit Card",
            "Student Loan",
            "Mortgage",
            "Auto Loan",
            "Personal Loan",
            "Tax Debt",
            "Other",
        ]

    if "accounts" not in st.session_state:
        st.session_state.accounts = []

    if "snapshots" not in st.session_state:
        st.session_state.snapshots = []


init_state()


def accounts_df():
    if st.session_state.accounts:
        return pd.DataFrame(st.session_state.accounts)
    return pd.DataFrame(columns=["Account Name", "Section", "Type", "Notes"])



def snapshots_df():
    if st.session_state.snapshots:
        df = pd.DataFrame(st.session_state.snapshots)
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    return pd.DataFrame(columns=["Date", "Account Name", "Section", "Type", "Amount", "Notes"])


def parse_amount(value):
    cleaned = str(value).replace(",", "").replace("$", "").strip()
    if cleaned == "":
        return 0.0
    return float(cleaned)


with st.sidebar:
    st.header("Manage Types")

    st.subheader("Add Asset Type")
    new_asset_type = st.text_input("New asset type", key="new_asset_type")
    if st.button("Add asset type"):
        value = new_asset_type.strip()
        if value and value not in st.session_state.asset_types:
            st.session_state.asset_types.append(value)
            st.success(f"Added asset type: {value}")
        elif value:
            st.warning("That asset type already exists.")

    st.subheader("Add Debt Type")
    new_debt_type = st.text_input("New debt type", key="new_debt_type")
    if st.button("Add debt type"):
        value = new_debt_type.strip()
        if value and value not in st.session_state.debt_types:
            st.session_state.debt_types.append(value)
            st.success(f"Added debt type: {value}")
        elif value:
            st.warning("That debt type already exists.")

    st.divider()
    st.write("**Current asset types**")
    st.write(", ".join(st.session_state.asset_types))

    st.write("**Current debt types**")
    st.write(", ".join(st.session_state.debt_types))


accounts_tab, update_tab, dashboard_tab, data_tab = st.tabs([
    "Accounts",
    "Update Balances",
    "Dashboard",
    "Data",
])


with accounts_tab:
    st.subheader("Accounts")
    st.write("Create the accounts you want to track over time. You only need to create each account once.")

    with st.form("account_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            account_name = st.text_input("Account name", placeholder="Example: Fidelity 401(k)")
            section = st.selectbox("Is this an asset or debt?", ["Asset", "Debt"])
        with col2:
            type_options = st.session_state.asset_types if section == "Asset" else st.session_state.debt_types
            selected_type = st.selectbox(
                "Asset or debt type",
                type_options,
            )
            account_notes = st.text_input("Notes", placeholder="Optional")

        add_account = st.form_submit_button("Add account")
        if add_account:
            existing_names = {a["Account Name"].strip().lower() for a in st.session_state.accounts}
            if not account_name.strip():
                st.error("Please enter an account name.")
            elif account_name.strip().lower() in existing_names:
                st.error("That account already exists.")
            else:
                st.session_state.accounts.append(
                    {
                        "Account Name": account_name.strip(),
                        "Section": section,
                        "Type": selected_type,
                        "Notes": account_notes.strip(),
                    }
                )
                st.success("Account added.")

    current_accounts = accounts_df()
    if not current_accounts.empty:
        st.dataframe(current_accounts.sort_values(by=["Section", "Type", "Account Name"]), use_container_width=True, hide_index=True)
    else:
        st.info("No accounts yet. Add your first asset or debt account.")


with update_tab:
    st.subheader("Update Balances")
    st.write("Enter one full snapshot for a date by updating all tracked accounts.")

    current_accounts = accounts_df()
    if current_accounts.empty:
        st.info("Add accounts first before entering balances.")
    else:
        snapshot_date = st.date_input("Snapshot date", value=date.today(), key="snapshot_date")
        previous_snapshots = snapshots_df()

        existing_for_date = previous_snapshots[
            previous_snapshots["Date"].dt.date == snapshot_date
        ] if not previous_snapshots.empty else pd.DataFrame()

        previous_by_account = {}
        if not previous_snapshots.empty:
            latest_previous = (
                previous_snapshots.sort_values(by=["Date"]) 
                .drop_duplicates(subset=["Account Name"], keep="last")
            )
            previous_by_account = latest_previous.set_index("Account Name")["Amount"].to_dict()

        with st.form("snapshot_form"):
            balance_rows = []
            parse_errors = []
            for _, row in current_accounts.sort_values(by=["Section", "Type", "Account Name"]).iterrows():
                account = row["Account Name"]
                prefill = 0.0

                if not existing_for_date.empty and account in existing_for_date["Account Name"].values:
                    prefill = float(existing_for_date.loc[existing_for_date["Account Name"] == account, "Amount"].iloc[0])
                elif account in previous_by_account:
                    prefill = float(previous_by_account[account])

                cols = st.columns([2, 1])
                cols[0].markdown(f"**{account}**  
{row['Section']} | {row['Type']}")
                amount_text = cols[1].text_input(
                    f"Amount for {account}",
                    value=f"{prefill:,.2f}",
                    key=f"amount_{snapshot_date}_{account}",
                    label_visibility="collapsed",
                    help="You can type large values with commas, like 125,000.50",
                )

                try:
                    parsed_amount = parse_amount(amount_text)
                except ValueError:
                    parsed_amount = None
                    parse_errors.append(account)

                balance_rows.append(
                    {
                        "Date": pd.to_datetime(snapshot_date),
                        "Account Name": account,
                        "Section": row["Section"],
                        "Type": row["Type"],
                        "Amount": parsed_amount,
                        "Notes": row["Notes"],
                    }
                )

            save_snapshot = st.form_submit_button("Save full snapshot")
            if save_snapshot:
                if parse_errors:
                    st.error("Please fix the amount format for: " + ", ".join(parse_errors))
                else:
                    st.session_state.snapshots = [
                        s for s in st.session_state.snapshots
                        if pd.to_datetime(s["Date"]).date() != snapshot_date
                    ]
                    st.session_state.snapshots.extend(balance_rows)
                    st.success("Snapshot saved for all accounts on that date.")

        if not existing_for_date.empty:
            st.caption("A snapshot already existed for this date. Saving will replace it.")


with dashboard_tab:
    st.subheader("Dashboard")

    df = snapshots_df()
    if df.empty:
        st.info("Add accounts and save at least one full snapshot to view the dashboard.")
    else:
        assets_total = float(df[df["Section"] == "Asset"]["Amount"].sum())
        debts_total = float(df[df["Section"] == "Debt"]["Amount"].sum())

        latest_date = df["Date"].max().date()
        latest_df = df[df["Date"].dt.date == latest_date]
        latest_assets = float(latest_df[latest_df["Section"] == "Asset"]["Amount"].sum())
        latest_debts = float(latest_df[latest_df["Section"] == "Debt"]["Amount"].sum())
        latest_net_worth = latest_assets - latest_debts

        col1, col2, col3 = st.columns(3)
        col1.metric("Assets", f"${latest_assets:,.2f}")
        col2.metric("Debts", f"${latest_debts:,.2f}")
        col3.metric("Net Worth", f"${latest_net_worth:,.2f}")

        timeline = (
            df.groupby([df["Date"].dt.date, "Section"])["Amount"]
            .sum()
            .unstack(fill_value=0)
            .reset_index()
            .rename(columns={"Date": "Snapshot Date"})
        )

        if "Asset" not in timeline.columns:
            timeline["Asset"] = 0.0
        if "Debt" not in timeline.columns:
            timeline["Debt"] = 0.0

        timeline["Net Worth"] = timeline["Asset"] - timeline["Debt"]
        timeline = timeline.sort_values(by="Date") if "Date" in timeline.columns else timeline.sort_values(by="Snapshot Date")

        st.markdown("### Net Worth Over Time")
        chart_df = timeline[["Snapshot Date", "Net Worth"]].set_index("Snapshot Date")
        st.line_chart(chart_df)

        st.markdown("### Snapshot History")
        display_timeline = timeline.rename(columns={
            "Asset": "Assets",
            "Debt": "Debts",
        })
        st.dataframe(display_timeline, use_container_width=True, hide_index=True)

        st.markdown("### Latest Snapshot Details")
        st.dataframe(
            latest_df.sort_values(by=["Section", "Type", "Account Name"]),
            use_container_width=True,
            hide_index=True,
        )


with data_tab:
    st.subheader("Data")
    st.write("Export your current data or upload saved files to continue from a previous session.")

    current_accounts = accounts_df()
    current_snapshots = snapshots_df()

    export_col1, export_col2 = st.columns(2)
    with export_col1:
        if not current_accounts.empty:
            st.download_button(
                "Download accounts CSV",
                data=current_accounts.to_csv(index=False),
                file_name="accounts.csv",
                mime="text/csv",
            )
    with export_col2:
        if not current_snapshots.empty:
            st.download_button(
                "Download snapshots CSV",
                data=current_snapshots.to_csv(index=False),
                file_name="snapshots.csv",
                mime="text/csv",
            )

    st.markdown("### Upload saved data")
    uploaded_accounts = st.file_uploader("Upload accounts CSV", type=["csv"], key="upload_accounts")
    uploaded_snapshots = st.file_uploader("Upload snapshots CSV", type=["csv"], key="upload_snapshots")

    if st.button("Load uploaded data"):
        loaded_any = False

        if uploaded_accounts is not None:
            df_accounts = pd.read_csv(uploaded_accounts)
            required_account_cols = {"Account Name", "Section", "Type", "Notes"}
            if required_account_cols.issubset(df_accounts.columns):
                st.session_state.accounts = df_accounts[ ["Account Name", "Section", "Type", "Notes"] ].to_dict("records")
                loaded_any = True
            else:
                st.error("Accounts CSV is missing required columns.")

        if uploaded_snapshots is not None:
            df_snapshots = pd.read_csv(uploaded_snapshots)
            required_snapshot_cols = {"Date", "Account Name", "Section", "Type", "Amount", "Notes"}
            if required_snapshot_cols.issubset(df_snapshots.columns):
                df_snapshots["Date"] = pd.to_datetime(df_snapshots["Date"])
                st.session_state.snapshots = df_snapshots[["Date", "Account Name", "Section", "Type", "Amount", "Notes"]].to_dict("records")
                loaded_any = True
            else:
                st.error("Snapshots CSV is missing required columns.")

        if loaded_any:
            account_types_asset = current_accounts[current_accounts["Section"] == "Asset"]["Type"].tolist() if not current_accounts.empty else []
            account_types_debt = current_accounts[current_accounts["Section"] == "Debt"]["Type"].tolist() if not current_accounts.empty else []
            if uploaded_accounts is not None:
                refreshed_accounts = accounts_df()
                st.session_state.asset_types = sorted(list(set(st.session_state.asset_types + refreshed_accounts[refreshed_accounts["Section"] == "Asset"]["Type"].dropna().tolist())))
                st.session_state.debt_types = sorted(list(set(st.session_state.debt_types + refreshed_accounts[refreshed_accounts["Section"] == "Debt"]["Type"].dropna().tolist())))
            st.success("Uploaded data loaded into this session.")


st.divider()
st.caption("Prototype version with reusable accounts, full-date snapshots, dashboard trend chart, and CSV import/export.")

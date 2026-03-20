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
            "Money Market",
            "Certificate of Deposit",
            "Brokerage",
            "Retirement",
            "HSA",
            "529 Plan",
            "Real Estate",
            "Vehicle",
            "Physical Item",
            "Business Ownership",
            "Crypto",
            "Other",
        ]

    if "liability_types" not in st.session_state:
        st.session_state.liability_types = [
            "Credit Card",
            "Student Loan",
            "Mortgage",
            "HELOC",
            "Auto Loan",
            "Personal Loan",
            "Medical Debt",
            "Tax Debt",
            "Business Loan",
            "Buy Now Pay Later",
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
    return pd.DataFrame(columns=["Account Name", "Section", "Type"])


def snapshots_df():
    if st.session_state.snapshots:
        df = pd.DataFrame(st.session_state.snapshots)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        return df
    return pd.DataFrame(columns=["Date", "Account Name", "Section", "Type", "Amount"])


def parse_amount(value):
    cleaned = str(value).replace(",", "").replace("$", "").strip()
    if cleaned == "":
        return 0.0
    return float(cleaned)


with st.sidebar:
    st.header("How to use this app")
    st.markdown("""
**Accounts**  
Create the accounts you want to track over time. Add asset accounts at the top of the Accounts tab and liability accounts below. You only need to create each account once.

**Update Balances**  
Enter a full snapshot for a selected date by updating all tracked accounts. Use positive numbers for everything. Do not enter liabilities as negative values.

**Dashboard**  
Review your latest assets, liabilities, net worth, and the net worth trend over time.

**Download/Upload**  
Download your accounts and snapshots as CSV files, or upload saved CSV files to resume from a previous session.

**Important**  
This app does not store data permanently. To continue using your data later, download your CSV files before closing or refreshing the app.
""")


accounts_tab, update_tab, dashboard_tab, data_tab = st.tabs([
    "Accounts",
    "Update Balances",
    "Dashboard",
    "Download/Upload",
])


with accounts_tab:
    st.subheader("Accounts")
    st.write("Create the accounts you want to track over time. Add asset accounts at the top and liability accounts below.")

    st.markdown("### Add Asset Account")
    with st.form("asset_account_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            asset_account_name = st.text_input("Asset account name", placeholder="Example: Fidelity 401(k)")
        with col2:
            asset_selected_type = st.selectbox("Asset type", st.session_state.asset_types, key="asset_type_select")

        add_asset_account = st.form_submit_button("Add asset account")
        if add_asset_account:
            existing_names = {a["Account Name"].strip().lower() for a in st.session_state.accounts}
            if not asset_account_name.strip():
                st.error("Please enter an asset account name.")
            elif asset_account_name.strip().lower() in existing_names:
                st.error("That account already exists.")
            else:
                st.session_state.accounts.append(
                    {
                        "Account Name": asset_account_name.strip(),
                        "Section": "Asset",
                        "Type": asset_selected_type,
                    }
                )
                st.success("Asset account added.")

    st.markdown("### Add Liability Account")
    with st.form("liability_account_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            liability_account_name = st.text_input("Liability account name", placeholder="Example: Chase Visa")
        with col2:
            liability_selected_type = st.selectbox(
                "Liability type",
                st.session_state.liability_types,
                key="liability_type_select",
            )

        add_liability_account = st.form_submit_button("Add liability account")
        if add_liability_account:
            existing_names = {a["Account Name"].strip().lower() for a in st.session_state.accounts}
            if not liability_account_name.strip():
                st.error("Please enter a liability account name.")
            elif liability_account_name.strip().lower() in existing_names:
                st.error("That account already exists.")
            else:
                st.session_state.accounts.append(
                    {
                        "Account Name": liability_account_name.strip(),
                        "Section": "Liability",
                        "Type": liability_selected_type,
                    }
                )
                st.success("Liability account added.")

    st.markdown("### Current Accounts")
    current_accounts = accounts_df()
    if not current_accounts.empty:
        st.dataframe(
            current_accounts.sort_values(by=["Section", "Type", "Account Name"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No accounts yet. Add your first asset or liability account.")


with update_tab:
    st.subheader("Update Balances")
    st.write(
        "Enter one full snapshot for a date by updating all tracked accounts. "
        "Use positive numbers for both assets and liabilities. "
        "Do not enter liabilities as negative values."
    )

    current_accounts = accounts_df()
    if current_accounts.empty:
        st.info("Add accounts first before entering balances.")
    else:
        snapshot_date = st.date_input("Snapshot date", value=date.today(), key="snapshot_date")
        previous_snapshots = snapshots_df()

        if not previous_snapshots.empty:
            existing_for_date = previous_snapshots[previous_snapshots["Date"].dt.date == snapshot_date]
            latest_previous = (
                previous_snapshots
                .sort_values(by=["Date"])
                .drop_duplicates(subset=["Account Name"], keep="last")
            )
            previous_by_account = latest_previous.set_index("Account Name")["Amount"].to_dict()
        else:
            existing_for_date = pd.DataFrame()
            previous_by_account = {}

        with st.form("snapshot_form"):
            balance_rows = []
            parse_errors = []

            for _, row in current_accounts.sort_values(by=["Section", "Type", "Account Name"]).iterrows():
                account = row["Account Name"]
                prefill = 0.0

                if not existing_for_date.empty and account in existing_for_date["Account Name"].values:
                    prefill = float(
                        existing_for_date.loc[
                            existing_for_date["Account Name"] == account,
                            "Amount",
                        ].iloc[0]
                    )
                elif account in previous_by_account:
                    prefill = float(previous_by_account[account])

                cols = st.columns([2, 1])
                cols[0].markdown(f"**{account}**  \n{row['Section']} | {row['Type']}")
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
        latest_date = df["Date"].max().date()
        latest_df = df[df["Date"].dt.date == latest_date].copy()

        latest_assets = float(latest_df[latest_df["Section"] == "Asset"]["Amount"].sum())
        latest_liabilities = float(latest_df[latest_df["Section"] == "Liability"]["Amount"].sum())
        latest_net_worth = latest_assets - latest_liabilities

        col1, col2, col3 = st.columns(3)
        col1.metric("Assets", f"${latest_assets:,.2f}")
        col2.metric("Liabilities", f"${latest_liabilities:,.2f}")
        col3.metric("Net Worth", f"${latest_net_worth:,.2f}")

        timeline = (
            df.assign(Snapshot_Date=df["Date"].dt.date)
            .groupby(["Snapshot_Date", "Section"], as_index=False)["Amount"]
            .sum()
            .pivot(index="Snapshot_Date", columns="Section", values="Amount")
            .fillna(0)
            .reset_index()
        )

        if "Asset" not in timeline.columns:
            timeline["Asset"] = 0.0
        if "Liability" not in timeline.columns:
            timeline["Liability"] = 0.0

        timeline["Net Worth"] = timeline["Asset"] - timeline["Liability"]
        timeline = timeline.sort_values(by="Snapshot_Date")

        st.markdown("### Net Worth Over Time")
        chart_df = timeline[["Snapshot_Date", "Net Worth"]].set_index("Snapshot_Date")
        st.line_chart(chart_df)

        st.markdown("### Snapshot History")
        display_timeline = timeline.rename(
            columns={
                "Snapshot_Date": "Snapshot Date",
                "Asset": "Assets",
                "Liability": "Liabilities",
            }
        )
        st.dataframe(display_timeline, use_container_width=True, hide_index=True)

        st.markdown("### Latest Snapshot Details")
        st.dataframe(
            latest_df.sort_values(by=["Section", "Type", "Account Name"]),
            use_container_width=True,
            hide_index=True,
        )


with data_tab:
    st.subheader("Download/Upload")
    st.write("Download your current data or upload saved files to continue from a previous session.")

    st.warning(
        "Your data is only stored for the current session. "
        "To reuse the app later, download both CSV files and upload them next time."
    )

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
            try:
                df_accounts = pd.read_csv(uploaded_accounts)
                required_account_cols = {"Account Name", "Section", "Type"}
                if required_account_cols.issubset(df_accounts.columns):
                    df_accounts = df_accounts[["Account Name", "Section", "Type"]].fillna("")
                    st.session_state.accounts = df_accounts.to_dict("records")
                    loaded_any = True
                else:
                    st.error("Accounts CSV is missing required columns: Account Name, Section, Type")
            except Exception as e:
                st.error(f"Could not load accounts CSV: {e}")

        if uploaded_snapshots is not None:
            try:
                df_snapshots = pd.read_csv(uploaded_snapshots)
                required_snapshot_cols = {"Date", "Account Name", "Section", "Type", "Amount"}
                if required_snapshot_cols.issubset(df_snapshots.columns):
                    df_snapshots = df_snapshots[
                        ["Date", "Account Name", "Section", "Type", "Amount"]
                    ].copy()
                    df_snapshots["Date"] = pd.to_datetime(df_snapshots["Date"], errors="coerce")
                    df_snapshots["Amount"] = pd.to_numeric(df_snapshots["Amount"], errors="coerce")
                    df_snapshots = df_snapshots.dropna(subset=["Date", "Amount"])
                    df_snapshots = df_snapshots.fillna("")
                    st.session_state.snapshots = df_snapshots.to_dict("records")
                    loaded_any = True
                else:
                    st.error(
                        "Snapshots CSV is missing required columns: "
                        "Date, Account Name, Section, Type, Amount"
                    )
            except Exception as e:
                st.error(f"Could not load snapshots CSV: {e}")

        if loaded_any:
            st.success("Uploaded data loaded into this session.")
            st.rerun()


st.divider()
st.caption(
    "Prototype version with reusable accounts, full-date snapshots, dashboard trend chart, "
    "and CSV import/export. Data is not stored permanently unless you download your CSV files."
)

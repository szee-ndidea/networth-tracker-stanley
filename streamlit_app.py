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
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
        df = df.dropna(subset=["Date", "Amount"])
        return df
    return pd.DataFrame(columns=["Date", "Account Name", "Section", "Type", "Amount"])



def rebuild_accounts_from_snapshots():
    df = snapshots_df()
    if not df.empty:
        st.session_state.accounts = (
            df[["Account Name", "Section", "Type"]]
            .dropna()
            .drop_duplicates()
            .sort_values(by=["Section", "Type", "Account Name"])
            .to_dict("records")
        )
    else:
        st.session_state.accounts = []



def parse_amount(value):
    cleaned = str(value).replace(",", "").replace("$", "").strip()
    if cleaned == "":
        return 0.0
    return float(cleaned)



def build_timeline(df):
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
    timeline["Snapshot_Date"] = pd.to_datetime(timeline["Snapshot_Date"])
    timeline = timeline.sort_values(by="Snapshot_Date")
    return timeline


with st.sidebar:
    st.header("How to use this app")
    st.markdown("""
**Add/Edit Accounts**  
Create the accounts you want to track over time. Add asset accounts at the top and liability accounts below. Use the account editor to update an existing account's name or type.

**Update Balances**  
Enter a full snapshot for a selected date by updating all tracked accounts. Use positive numbers for everything. Do not enter liabilities as negative values.

**Dashboard**  
Review your latest assets, liabilities, net worth, current trend, and goal planning metrics.

**Download/Upload**  
Download your net worth data as one CSV file, or upload that saved CSV file to resume from a previous session.

**Important**  
This app does not store data permanently. To continue using your data later, download your CSV file before closing or refreshing the app.
""")


accounts_tab, update_tab, dashboard_tab, data_tab = st.tabs([
    "Add/Edit Accounts",
    "Update Balances",
    "Dashboard",
    "Download/Upload",
])


with accounts_tab:
    current_accounts = accounts_df()

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
                st.rerun()

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
                st.rerun()

    st.markdown("### Current Accounts")
    if not current_accounts.empty:
        editable_accounts = current_accounts.sort_values(by=["Section", "Type", "Account Name"]).reset_index(drop=True).copy()
        editable_accounts.insert(0, "Edit", False)

        edited_accounts = st.data_editor(
            editable_accounts,
            use_container_width=True,
            hide_index=True,
            disabled=["Section", "Account Name", "Type"],
            column_config={
                "Edit": st.column_config.CheckboxColumn("Edit", help="Select one account to edit below"),
                "Account Name": st.column_config.TextColumn("Account Name"),
                "Section": st.column_config.TextColumn("Section"),
                "Type": st.column_config.TextColumn("Type"),
            },
            key="accounts_editor",
        )

        selected_rows = edited_accounts[edited_accounts["Edit"] == True]

        if len(selected_rows) == 1:
            selected_index = selected_rows.index[0]
            original_name = editable_accounts.loc[selected_index, "Account Name"]
            original_section = editable_accounts.loc[selected_index, "Section"]
            original_type = editable_accounts.loc[selected_index, "Type"]
            valid_types = st.session_state.asset_types if original_section == "Asset" else st.session_state.liability_types
            type_index = valid_types.index(original_type) if original_type in valid_types else 0

            st.markdown("### Edit Selected Account")
            with st.form("edit_account_form"):
                edit_col1, edit_col2 = st.columns(2)
                with edit_col1:
                    edited_account_name = st.text_input("Account name", value=original_name)
                with edit_col2:
                    edited_account_type = st.selectbox(
                        "Type",
                        valid_types,
                        index=type_index,
                        key="edit_account_type_select",
                    )

                save_account_changes = st.form_submit_button("Save account changes")
                if save_account_changes:
                    existing_names = {a["Account Name"].strip().lower() for a in st.session_state.accounts}
                    old_name_lower = original_name.strip().lower()
                    new_name_lower = edited_account_name.strip().lower()

                    if not edited_account_name.strip():
                        st.error("Please enter an account name.")
                    elif new_name_lower != old_name_lower and new_name_lower in existing_names:
                        st.error("That account name already exists.")
                    else:
                        for account in st.session_state.accounts:
                            if account["Account Name"] == original_name and account["Section"] == original_section:
                                account["Account Name"] = edited_account_name.strip()
                                account["Type"] = edited_account_type

                        for snapshot in st.session_state.snapshots:
                            if snapshot["Account Name"] == original_name and snapshot["Section"] == original_section:
                                snapshot["Account Name"] = edited_account_name.strip()
                                snapshot["Type"] = edited_account_type

                        st.success("Account updated.")
                        st.rerun()
        elif len(selected_rows) > 1:
            st.info("Select only one account in the table to edit it.")
    else:
        st.info("No accounts yet. Add your first asset or liability account.")


with update_tab:
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
                .drop_duplicates(subset=["Account Name", "Section"], keep="last")
            )
            previous_by_account = {
                (row["Account Name"], row["Section"]): row["Amount"]
                for _, row in latest_previous.iterrows()
            }
        else:
            existing_for_date = pd.DataFrame()
            previous_by_account = {}

        with st.form("snapshot_form"):
            balance_rows = []
            parse_errors = []

            for _, row in current_accounts.sort_values(by=["Section", "Type", "Account Name"]).iterrows():
                account = row["Account Name"]
                section = row["Section"]
                prefill = 0.0

                if not existing_for_date.empty and ((existing_for_date["Account Name"] == account) & (existing_for_date["Section"] == section)).any():
                    prefill = float(
                        existing_for_date.loc[
                            (existing_for_date["Account Name"] == account) & (existing_for_date["Section"] == section),
                            "Amount",
                        ].iloc[0]
                    )
                elif (account, section) in previous_by_account:
                    prefill = float(previous_by_account[(account, section)])

                cols = st.columns([2, 1])
                cols[0].markdown(f"**{account}**  \n{row['Section']} | {row['Type']}")
                amount_text = cols[1].text_input(
                    f"Amount for {account} {section}",
                    value=f"{prefill:,.2f}",
                    key=f"amount_{snapshot_date}_{section}_{account}",
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

        timeline = build_timeline(df)

        st.markdown("### Net Worth Over Time")
        chart_df = timeline[["Snapshot_Date", "Net Worth"]].set_index("Snapshot_Date")
        st.line_chart(chart_df)

        st.markdown("### Goal Planning")
        today_date = date.today()
        goal_col1, goal_col2 = st.columns(2)
        with goal_col1:
            st.metric("Net Worth Today", f"${latest_net_worth:,.2f}")
            st.caption(f"Using latest snapshot from {latest_date.strftime('%B %d, %Y')} as of today, {today_date.strftime('%B %d, %Y')}.")
        with goal_col2:
            goal_net_worth = st.number_input("Goal net worth", min_value=0.0, step=10000.0, format="%.2f")
            goal_end_date = st.date_input("Goal end date", value=today_date.replace(year=today_date.year + 10), min_value=today_date)

        days_to_goal = (goal_end_date - today_date).days
        if days_to_goal <= 0:
            st.error("Choose a goal end date after today.")
        elif goal_net_worth <= 0:
            st.info("Enter a goal net worth and end date to calculate the required yearly increase.")
        else:
            total_increase_needed = goal_net_worth - latest_net_worth
            years_to_goal = days_to_goal / 365.25
            yearly_increase_needed = total_increase_needed / years_to_goal if years_to_goal > 0 else 0.0
            monthly_increase_needed = yearly_increase_needed / 12

            goal_metric_1, goal_metric_2, goal_metric_3 = st.columns(3)
            goal_metric_1.metric("Years to goal", f"{years_to_goal:,.1f}")
            goal_metric_2.metric("Increase needed per year", f"${yearly_increase_needed:,.2f}")
            goal_metric_3.metric("Increase needed per month", f"${monthly_increase_needed:,.2f}")

            if total_increase_needed <= 0:
                st.success("You are already at or above this goal based on your latest snapshot.")
            else:
                st.info(f"To grow from ${latest_net_worth:,.2f} to ${goal_net_worth:,.2f} by {goal_end_date.strftime('%B %d, %Y')}, you would need an average net worth increase of ${yearly_increase_needed:,.2f} per year.")


with data_tab:
    st.warning(
        "Your data is only stored for the current session. "
        "To reuse the app later, download your CSV file and upload it next time."
    )

    current_snapshots = snapshots_df()

    if not current_snapshots.empty:
        export_df = current_snapshots.sort_values(by=["Date", "Section", "Type", "Account Name"])
        st.download_button(
            "Download net worth CSV",
            data=export_df.to_csv(index=False),
            file_name="networth_data.csv",
            mime="text/csv",
        )

    st.markdown("### Upload saved data")
    uploaded_data = st.file_uploader("Upload net worth CSV", type=["csv"], key="upload_networth_data")

    if st.button("Load uploaded data"):
        if uploaded_data is not None:
            try:
                df = pd.read_csv(uploaded_data)
                required_cols = {"Date", "Account Name", "Section", "Type", "Amount"}
                if required_cols.issubset(df.columns):
                    df = df[["Date", "Account Name", "Section", "Type", "Amount"]].copy()
                    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
                    df = df.dropna(subset=["Date", "Account Name", "Section", "Type", "Amount"])
                    df["Account Name"] = df["Account Name"].astype(str).str.strip()
                    df["Section"] = df["Section"].astype(str).str.strip()
                    df["Type"] = df["Type"].astype(str).str.strip()

                    st.session_state.snapshots = df.to_dict("records")
                    rebuild_accounts_from_snapshots()
                    st.success("Uploaded data loaded into this session.")
                    st.rerun()
                else:
                    st.error("CSV is missing required columns: Date, Account Name, Section, Type, Amount")
            except Exception as e:
                st.error(f"Could not load CSV: {e}")
        else:
            st.error("Please upload a CSV file first.")


st.divider()
st.caption(
    "Prototype version with reusable accounts, full-date snapshots, dashboard trend chart, "
    "goal planning, and single-file CSV import/export. Data is not stored permanently unless you download your CSV file."
)

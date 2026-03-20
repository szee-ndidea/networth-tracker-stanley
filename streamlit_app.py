st.markdown("### Edit Account Name")
with st.form("rename_account_form", clear_on_submit=True):
    account_to_rename = st.selectbox(
        "Select account to rename",
        current_accounts.sort_values(by=["Account Name"])["Account Name"].tolist(),
    )
    new_account_name = st.text_input("New account name")

    rename_account = st.form_submit_button("Rename account")
    if rename_account:
        existing_names = {a["Account Name"].strip().lower() for a in st.session_state.accounts}
        old_name_lower = account_to_rename.strip().lower()
        new_name_lower = new_account_name.strip().lower()

        if not new_account_name.strip():
            st.error("Please enter a new account name.")
        elif new_name_lower != old_name_lower and new_name_lower in existing_names:
            st.error("That account name already exists.")
        else:
            for account in st.session_state.accounts:
                if account["Account Name"] == account_to_rename:
                    account["Account Name"] = new_account_name.strip()

            for snapshot in st.session_state.snapshots:
                if snapshot["Account Name"] == account_to_rename:
                    snapshot["Account Name"] = new_account_name.strip()

            st.success("Account name updated.")
            st.rerun()

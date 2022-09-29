import datetime
from decimal import InvalidOperation
import decimal
from multiprocessing.sharedctypes import Value
from dateutil.parser import parse
import pandas as pd
import account
import transaction
import logging

logging.basicConfig(filename='supportbank.log',filemode='w',level=logging.DEBUG)

# CONSTANTS {{{
# TRANSACTIONS_FILE   = './transactions2014.csv'
TRANSACTIONS_FILE   = './dodgytransactions2015.csv'
DEBUG               = False

LIST_ALL            = 1
LIST_NAME           = 2
QUIT_MENU           = 3

ID_RESPONSE         = 1
# }}}

def create_accounts(transactions_df):
    accounts = {}
    for id in transactions_df['From']:
        if not id in accounts:
            accounts[str(id)] = account.Account(str(id))
    return accounts

def is_date(string, fuzzy=False):
    try:
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False

def perform_transactions(transactions_df, accounts):
    line_no = 0
    for t in transactions_df.iloc:
        try:
            new_transaction = transaction.Transaction(t['Date'],t['From'],t['To'],t['Narrative'],t['Amount'])
            if not (is_date(t['Date'])):
                raise ValueError()

            accounts[t['From']].transaction_history.append(new_transaction)
            accounts[t['To']].transaction_history.append(new_transaction)

            accounts[t['From']].balance -= decimal.Decimal(t['Amount'])
            accounts[t['To']].balance   += decimal.Decimal(t['Amount'])
        except InvalidOperation:
            logging.error(f'{curr_time()}: Invalid amount on line {line_no}')
        except ValueError:
            logging.error(f'{curr_time()}: Invalid date on line {line_no}')
        line_no += 1
    return accounts

def pre_process():
    transactions_df = pd.read_csv(TRANSACTIONS_FILE)
    logging.info(f'{curr_time()}: Read csv {TRANSACTIONS_FILE}')
    transactions_df['Amount']
    if DEBUG:
        print(transactions_df['Amount'])
        print(transactions_df.iloc[0])

    accounts = create_accounts(transactions_df)
    if DEBUG:
        print(accounts['Jon A'].account_id)

    return perform_transactions(transactions_df, accounts)

def print_menu():
    print('========================MAIN MENU===============================')
    print('Option    Alternate    Description')
    print('1)        List All     Output name and balance of each person')
    print('2 [Name]) List [Name]  Output transaction history for *NAME*')
    print('3)        Quit         Quit program')
    print('================================================================')

def menu_choice():
    selection = ''
    id = ''
    while selection == '':
        response = input('Select menu option: ')
        if response.lower() in ['1', 'list all']:
            selection = LIST_ALL
        elif response.lower()[4:] not in ['2','list'] and len(response.split()) >= 2:
            selection = LIST_NAME
            id = " ".join(response.split()[ID_RESPONSE:])
        elif response.lower() in ['3', 'quit', 'exit']:
            selection = QUIT_MENU
    return (selection,id)

def list_all_entries(updated_accounts):
    for id in updated_accounts:
        print(f'{id} £{decimal.Decimal(updated_accounts[id].balance)}')

def list_transaction_history(updated_accounts, id):
    if id in updated_accounts:
        for t in updated_accounts[id].transaction_history:
            t.print_transaction()
    else:
        print(f'Account name "{id}" not recognised')

def curr_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    logging.info(f'{curr_time()} Execution finished')
    updated_accounts = pre_process()
    selection = ''
    while selection != QUIT_MENU:
        print_menu()
        logging.info(f'{curr_time()}: Displaying menu')
        (selection,id) = menu_choice()
        if DEBUG:
            print(id)
        if selection == LIST_ALL:
            logging.info(f'{curr_time()}: List all selected')
            list_all_entries(updated_accounts)
        elif selection == LIST_NAME:
            logging.info(f'{curr_time()}: List {id} selected')
            list_transaction_history(updated_accounts, id)
        elif selection != QUIT_MENU:
            logging.info(f'{curr_time()}: Invalid menu option selected')
    logging.info(f'{curr_time()}: Execution finished')

if __name__ == '__main__':
    main()
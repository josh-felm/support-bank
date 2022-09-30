from curses.ascii import isdigit
import datetime
from decimal import *
import json
from multiprocessing.sharedctypes import Value
import os
from dateutil.parser import parse
import pandas as pd
import account
import xml.etree.ElementTree as ET
import transaction
import logging

logging.basicConfig(filename='supportbank.log',filemode='w',level=logging.DEBUG, format='%(asctime)s %(message)s')

# CONSTANTS {{{
TRANSACTIONS_FILE   = '.\\data\\transactions2012.xml'
DATA_DIR            = '.\\data'
OUT_DIR             = '.\\out'

DEBUG               = False

LIST_ALL            = 1
LIST_NAME           = 2
READ_FILE           = 3
WRITE_FILE          = 4
QUIT_MENU           = 5

ID_ARG         = 1

OLE_TIME_ZERO       = datetime.datetime(1899, 12, 30, 0, 0, 0)
# }}}

def is_date(string:str, fuzzy=False):
    try:
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False

def is_num(string:str):
    try:
        float(string)
        return True
    except ValueError:
        return False

def create_accounts(transactions_df):
    accounts = {}
    for id in transactions_df['From']:
        if not id in accounts:
            accounts[str(id)] = account.Account(str(id))
    return accounts

def perform_transactions(transactions_df, accounts):
    line_no = 0
    for t in transactions_df.iloc:
        try:
            new_transaction = transaction.Transaction(t['Date'],t['From'],t['To'],t['Narrative'],t['Amount'])
            if not (is_date(str(t['Date']))):
                raise ValueError()

            accounts[t['From']].transaction_history.append(new_transaction)
            accounts[t['To']].transaction_history.append(new_transaction)

            accounts[t['From']].balance -= int(t['Amount'])
            accounts[t['To']].balance   += int(t['Amount'])
        except InvalidOperation:
            logging.error(f'Invalid amount on line {line_no}')
        except ValueError:
            logging.error(f'Invalid date on line {line_no}')
        line_no += 1
    return accounts

def read_json(curr_file):
    new_headers = {'date':'Date','fromAccount':'From','toAccount':'To','narrative':'Narrative','amount':'Amount'}
    transactions_df = pd.DataFrame(pd.read_json(curr_file))
    transactions_df.rename(columns=new_headers,inplace=True)
    return transactions_df

def read_xml(curr_file):
    transactions_xml = ET.parse(curr_file)
    root = transactions_xml.getroot()
    column_headers = ['Date', 'From', 'To', 'Narrative', 'Amount']
    #NOTE: creating a dataframe from a list of lists is much more efficient than creating a DF line by line
    list_transactions = []
    for transaction in root.findall('SupportTransaction'):
        t_narrative = transaction.find('Description').text
        t_date      = datetime.datetime.strftime(OLE_TIME_ZERO + datetime.timedelta(days=int(transaction.get('Date'))), '%d/%m/%Y')
        t_amount    = transaction.find('Value').text
        t_from      = transaction.find('Parties').find('From').text
        t_to        = transaction.find('Parties').find('To').text
        list_transactions.append([t_date, t_from, t_to, t_narrative, t_amount])
    transactions_df = pd.DataFrame(list_transactions, columns=column_headers)
    return transactions_df

def write_file(file_name, curr_file):
    new_file_path = os.path.join(OUT_DIR, file_name)
    transactions_df = read_file(curr_file)
    print('Writing to ' + str(new_file_path))
    if file_name.endswith('.csv'):
        transactions_df.to_csv(new_file_path, index=False)
        print('Write successful')
        logging.info(f'Successful write to file {new_file_path}')
    elif file_name.endswith('.json'):
        result = transactions_df.to_json(orient='records')
        parsed = json.loads(result)
        with open(new_file_path, 'w') as f:
            json.dump(parsed, f, indent=4) 
    elif file_name.endswith('xml'):
        transactions_df.to_xml(new_file_path, index=False)

def read_file(curr_file):
    if curr_file.lower().endswith('.csv'):
        logging.info(f'filetype is csv')
        transactions_df = pd.read_csv(curr_file)
    elif curr_file.lower().endswith('.json'):
        logging.info(f'filetype is json')
        transactions_df = read_json(curr_file)
    elif curr_file.lower().endswith('.xml'):
        logging.info(f'filetype is xml')
        transactions_df = read_xml(curr_file)
    logging.info(f'Read file {curr_file}')
    print(f'Read file {curr_file}')
    return transactions_df

def pre_process(curr_file):
    transactions_df = read_file(curr_file)

    line_no = 0
    for amount in transactions_df['Amount']:
        if not (is_num(amount)):
            logging.warning(f'"{amount}" is not a numeric value at line {line_no}, transaction removed')
            transactions_df = transactions_df.drop(index=line_no)
        else:
            transactions_df.at[line_no, 'Amount'] = float(transactions_df['Amount'][line_no]) * 100
        line_no += 1

    if DEBUG:
        print(transactions_df['Amount'])
        print(transactions_df.iloc[0])

    accounts = create_accounts(transactions_df)
    if DEBUG:
        print(accounts['Jon A'].account_id)

    updated_accounts = perform_transactions(transactions_df, accounts)
    return updated_accounts

def print_menu(curr_file):
    COL_WIDTH = 90
    top_bar_width = int((COL_WIDTH - len('MAIN MENU: ' + curr_file))/2 - 1)
    top_bar_prompt = ' MAIN MENU: ' + curr_file + ' '
    print('='*top_bar_width + top_bar_prompt + '='*top_bar_width)
    print('{0:15} {1:17} {2:40}'.format('OPTION', 'ALTERNATE','DESCRIPTION'))
    print('{0:15} {1:17} {2:40}'.format('1', 'List All','Output name and balance of each account'))
    print('{0:15} {1:17} {2:40}'.format('2 [Name]', 'List [Name]','Output transaction history for *NAME*'))
    print('{0:15} {1:17} {2:40}'.format('3 [Filename]', 'Import [Filename]','Import file from disk (must be in "data" directory)'))
    print('{0:15} {1:17} {2:40}'.format('4 [Filename]', 'Export [Filename]','Export file to disk (will be written to "out" directory)'))
    print('{0:15} {1:17} {2:40}'.format('5', 'Quit','Exit program'))
    print('='*(len(top_bar_prompt) + 2*top_bar_width))

def menu_choice():
    selection = id = file_name = ''
    while selection == '':
        response = input('Select menu option: ')
        if response.lower() in [str(LIST_ALL), 'list all']:
            selection = LIST_ALL
        elif response.split()[0].lower() in [str(LIST_NAME),'list'] and len(response.split()) >= 2:
            selection = LIST_NAME
            id = " ".join(response.split()[ID_ARG:])
        elif response.split()[0].lower() in [str(READ_FILE), 'import', 'read'] and len(response.split()) >= 2:
            selection = READ_FILE
            file_name = response.split()[ID_ARG]
        elif response.split()[0].lower() in [str(WRITE_FILE), 'export', 'write'] and len(response.split()) >= 2:
            selection = WRITE_FILE
            file_name = response.split()[ID_ARG]
        elif response.lower() in [str(QUIT_MENU), 'quit', 'exit']:
            selection = QUIT_MENU
    return (selection,id,file_name)

def list_all_entries(updated_accounts):
    print('{0:15} {1:>7}'.format('ACCOUNT NAME', 'BALANCE'))
    for id in updated_accounts:
        print('{0:15} {1:>7}'.format(id, '£' + str(round(updated_accounts[id].balance/100,2))))

def list_transaction_history(updated_accounts, id):
    print(f'Transaction history for {id}')
    print(transaction.Transaction.PRINT_FORMAT.format('DATE', 'FROM', 'TO', 'NARRATIVE', 'AMOUNT'))
    if id in updated_accounts:
        for t in updated_accounts[id].transaction_history:
            t.print_transaction()
    else:
        logging.warning(f'{id} not present in selected file')
        print(f'Account name "{id}" not recognised')

def curr_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    logging.info(f'Execution started')
    curr_file = TRANSACTIONS_FILE
    if (curr_file.lower().endswith(('.json', '.csv', '.xml'))):
        updated_accounts = pre_process(curr_file)
        selection = ''
        while selection != QUIT_MENU:
            print_menu(curr_file)
            logging.info(f'Displaying menu')
            (selection,id,file_name) = menu_choice()
            if DEBUG:
                print(id)
            if selection == LIST_ALL:
                logging.info(f'List all selected')
                list_all_entries(updated_accounts)
            elif selection == LIST_NAME:
                logging.info(f'List {id} selected')
                list_transaction_history(updated_accounts, id)
            elif selection == READ_FILE:
                logging.info(f'Read file {file_name} selected')
                new_file_path = os.path.join(DATA_DIR, file_name)
                if os.path.isfile(new_file_path):
                    logging.info(f'Changing information to file {new_file_path}')
                    curr_file = new_file_path
                    updated_accounts = pre_process(curr_file)
                else:
                    print('File does not exist')
                    logging.warning(f'Requested file {new_file_path} does not exist')
            elif selection == WRITE_FILE:
                if file_name.endswith(('.csv', '.xml', '.json')):
                    write_file(file_name, curr_file)
                else:
                    print('That file format is not supported')
                    logging.warning(f'{curr_time}: File {file_name} not supported')
            elif selection != QUIT_MENU:
                logging.info(f'Invalid menu option selected')
            if selection != QUIT_MENU:
                input('Press enter to continue...')
                os.system('cls' if os.name == 'nt' else 'clear')
    else:
        logging.error(f'Invalid file format for transaction file')
    logging.info(f'Execution finished')

if __name__ == '__main__':
    main()
from tinydb import TinyDB, Query

db = TinyDB('nexworld.json')
players = db.table('players')
prefixes_table = db.table('prefixes')
market_table = db.table('market')
raids_table = db.table('raids')
mail_table = db.table('mail')

Player = Query()
Prefix = Query()


item_counter_table = db.table('item_counter')
ItemCounterQ = Query()
mail_counter_table = db.table('mail_counter')
MailCounterQ = Query()

def generate_item_uid():
    result = item_counter_table.search(ItemCounterQ.name == 'global_item_id')
    if not result:
        item_counter_table.insert({'name': 'global_item_id', 'value': 1})
        return '1'
    new_val = result[0]['value'] + 1
    item_counter_table.update({'value': new_val}, ItemCounterQ.name == 'global_item_id')
    return str(new_val)


def generate_mail_id():
    result = mail_counter_table.search(MailCounterQ.name == 'global_mail_id')
    if not result:
        mail_counter_table.insert({'name': 'global_mail_id', 'value': 1})
        return 1
    new_val = result[0]['value'] + 1
    mail_counter_table.update({'value': new_val}, MailCounterQ.name == 'global_mail_id')
    return new_val

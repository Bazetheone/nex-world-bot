# One place for rarity order and icons.
# To change an icon, replace the value with "<:name:id>" or a normal emoji.
RARITY_ORDER = ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary',
                'Mythic', 'Godly', 'Divine', 'Celestial', 'Special']

RARITY_ICONS = {
    'Common': '<:common:1568558283269079070>',
    'Uncommon': '<:uncommon:1568558339200131173>',
    'Rare': '<:rare:1568558392862048366>',
    'Epic': '<:epic:1568558434037669988>',
    'Legendary': '<:Legendary:1568558484159463566>',
    'Mythic': '<:mythic:1568558550941302794>',
    'Mythical': '<:mythic:1568558550941302794>',
    'Godly': '<:godly:1568558712925454407>',
    'Divine': '<:Divine:1568558600127778846>',
    'Celestial': '<:Celestial:1568558640430972987>',
    'Special': '✨',
}

ALIASES = {'Mythical': 'Mythic'}


def normalize(rarity):
    return ALIASES.get(rarity, rarity)


def rarity_icon(rarity):
    return RARITY_ICONS.get(normalize(rarity), '❔')


def rarity_rank(rarity):
    r = normalize(rarity)
    return RARITY_ORDER.index(r) if r in RARITY_ORDER else -1

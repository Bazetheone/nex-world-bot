# One place for rarity order and icons.
# To use a custom emoji later, replace the value with "<:name:id>".
RARITY_ORDER = ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary',
                'Mythic', 'Godly', 'Divine', 'Celestial', 'Special']

RARITY_ICONS = {
    'Common': '⚪', 'Uncommon': '🟢', 'Rare': '🔵', 'Epic': '🟣',
    'Legendary': '🟠', 'Mythic': '🔴', 'Godly': '🔱', 'Divine': '🟡',
    'Celestial': '💠', 'Special': '✨',
}

ALIASES = {'Mythical': 'Mythic'}


def normalize(rarity):
    return ALIASES.get(rarity, rarity)


def rarity_icon(rarity):
    return RARITY_ICONS.get(normalize(rarity), '❔')


def rarity_rank(rarity):
    r = normalize(rarity)
    return RARITY_ORDER.index(r) if r in RARITY_ORDER else -1

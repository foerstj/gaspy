from bits.bits import Bits
from printouts.common import load_enemies, Enemy
from printouts.csv import write_csv_dict


class EnemyAttack:
    def __init__(self, enemy: Enemy):
        self.enemy = enemy


def make_csv_line(attack: EnemyAttack) -> dict:
    return {
        'template': attack.enemy.template_name,
        'screen_name': attack.enemy.screen_name,
    }


def write_enemy_attacks_csv(bits: Bits):
    enemies = load_enemies(bits)
    attacks = [EnemyAttack(enemy) for enemy in enemies]

    keys = ['template', 'screen_name']
    header_dict = {'template': 'Template', 'screen_name': 'Screen Name'}
    data_dicts = [make_csv_line(a) for a in attacks]

    write_csv_dict('Enemy Attacks', keys, header_dict, data_dicts, ';')

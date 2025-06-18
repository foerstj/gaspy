from bits.bits import Bits
from printouts.common import load_enemies, Enemy
from printouts.csv import write_csv_dict


class EnemyAttack:
    def __init__(self, enemy: Enemy, stance: str):
        self.enemy = enemy
        self.stance = stance


def make_csv_line(attack: EnemyAttack) -> dict:
    return {
        'template': attack.enemy.template_name,
        'screen_name': attack.enemy.screen_name,
        'stance': attack.stance,
    }


def write_enemy_attacks_csv(bits: Bits):
    enemies = load_enemies(bits)
    attacks: list[EnemyAttack] = list()
    for enemy in enemies:
        if enemy.is_melee():
            attacks.append(EnemyAttack(enemy, 'Melee'))
        if enemy.is_ranged():
            attacks.append(EnemyAttack(enemy, 'Ranged'))
        if enemy.is_magic():
            attacks.append(EnemyAttack(enemy, 'Magic'))

    keys = ['template', 'screen_name', 'stance']
    header_dict = {'template': 'Template', 'screen_name': 'Screen Name', 'stance': 'Stance'}
    data_dicts = [make_csv_line(a) for a in attacks]

    write_csv_dict('Enemy Attacks', keys, header_dict, data_dicts, ';')

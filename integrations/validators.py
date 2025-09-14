import re
from typing import Iterable

from django.core.exceptions import ValidationError

UF_CHOICES: Iterable[str] = (
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
    "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
    "RS","RO","RR","SC","SP","SE","TO",
)


def validate_uf(uf: str) -> None:
    if str(uf).upper() not in UF_CHOICES:
        raise ValidationError("UF inválida")


def validate_cnpj(cnpj: str) -> None:
    digits = re.sub(r"\D", "", str(cnpj))
    if len(digits) != 14 or len(set(digits)) == 1:
        raise ValidationError("CNPJ inválido")

    nums = [int(n) for n in digits]

    def calc_digit(numbers: list[int], weights: list[int]) -> int:
        s = sum(n * w for n, w in zip(numbers, weights))
        r = s % 11
        return 0 if r < 2 else 11 - r

    d1 = calc_digit(nums[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = calc_digit(nums[:12] + [d1], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])

    if nums[12] != d1 or nums[13] != d2:
        raise ValidationError("CNPJ inválido")



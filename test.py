from typing import Dict, List, Optional, Sequence, Union
characters = {'A','G', 'C', 'T', 'N'}
_vocab_str_to_int = {
    "[CLS]": 0,
    "[SEP]": 1,
    "[BOS]": 2,
    "[MASK]": 3,
    "[PAD]": 4,
    "[RESERVED]": 5,
    "[UNK]": 6,
    **{ch: i + 7 for i, ch in enumerate(characters)},
}
_vocab_int_to_str = {v: k for k, v in _vocab_str_to_int.items()}
# print(_vocab_str_to_int, _vocab_int_to_str)
token = "AGCT"
id = _vocab_str_to_int.get(token, _vocab_str_to_int["[UNK]"])
print(id)


def _tokenize(text: str) -> List[str]:
    return list(text)

print(_tokenize("AGCTAA"))
from pathlib import Path


def create_poisoned_file(output_path: Path = Path("examples/poisoned-code/test_bug.py")) -> Path:
    cyrillic_a = chr(0x0430)
    zero_width_space = chr(0x200B)
    bidi_override = chr(0x202E)
    code_content = f'''def calculate_v{cyrillic_a}lue(input_val):
    result = input_val * 2{zero_width_space}
    note = "safe"  # {bidi_override} visually confusing comment
    return result
'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code_content, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = create_poisoned_file()
    print(f"Generated poisoned code sample: {path}")

import json
from pathlib import Path

from main import app

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
	output_path = BACKEND_ROOT / 'openapi.json'
	with open(output_path, 'w', encoding='utf-8') as f:
		json.dump(app.openapi(), f, ensure_ascii=False, indent=2)
		f.write('\n')
	print(f'OpenAPI schema generated: {output_path}')


if __name__ == '__main__':
	main()

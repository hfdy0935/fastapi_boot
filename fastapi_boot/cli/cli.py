import argparse
import os

from .template import gen_controller, gen_main_template


def main():
    parser = argparse.ArgumentParser(description="FastAPI Boot CLI")
    parser.add_argument('--host', type=str,
                        default='127.0.0.1', help='Host address')
    parser.add_argument('--port', type=int, default=8000, help='Port number')
    parser.add_argument('--reload', action='store_true',
                        help='Enable auto-reload')
    parser.add_argument('--name', type=str, default='demo',
                        help='name of first controller')

    args = parser.parse_args()
    if os.path.exists('./main.py'):
        raise Exception('File main.py already exists')
    if os.path.exists(f'./src/controller/{args.name}.py'):
        raise Exception(f'Dir ./src/controller/{args.name}.py already exists')
    with open('./main.py', 'w') as f:
        f.write(gen_main_template(args.host, args.port, args.reload, args.name))
    if not os.path.exists('./src/controller'):
        os.makedirs('./src/controller')
    with open(f'./src/controller/{args.name}.py', 'w') as f:
        f.write(gen_controller(args.name))


if __name__ == "__main__":
    main()

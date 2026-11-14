"""Local editor bridge client for isolated gameplay authoring."""
import json
import socket


def call(cmd, **params):
    with socket.create_connection(('127.0.0.1', 8765), timeout=60) as connection:
        connection.sendall((json.dumps({'cmd': cmd, 'params': params}) + '\n').encode())
        response = json.loads(connection.makefile('r', encoding='utf-8').readline())
    if not response.get('ok'):
        raise RuntimeError(json.dumps(response))
    return response.get('result', response)


def python(code):
    result = call('run_console_command', command='py ' + code, world='editor')
    if any('Error:' in line or 'Traceback' in line for line in result.get('log', [])):
        raise RuntimeError(json.dumps(result))
    return result


if __name__ == '__main__':
    import sys
    print(json.dumps(call(sys.argv[1], **json.loads(sys.argv[2] if len(sys.argv) > 2 else '{}')), indent=2))
